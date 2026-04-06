"""
Batch Processor

Efficient batch processing for high-throughput inference.
Supports parallel processing, memory management, and progress tracking.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Generator, Iterator, Sequence

import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from core.exceptions import ProcessingError
from core.types import AnalysisStatus

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class BatchItem:
    """
    Single item in a batch.
    
    Attributes:
        id: Unique identifier
        data: Input data (path, array, or bytes)
        priority: Processing priority (lower = higher priority)
        metadata: Additional metadata
    """
    
    id: str
    data: str | Path | np.ndarray | bytes
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other: "BatchItem") -> bool:
        """Compare by priority for priority queue."""
        return self.priority < other.priority


@dataclass
class BatchResult:
    """
    Result of batch processing.
    
    Attributes:
        id: Item identifier
        success: Whether processing succeeded
        result: Processing result
        error: Error message if failed
        processing_time: Time taken
    """
    
    id: str
    success: bool
    result: Any = None
    error: str | None = None
    processing_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "success": self.success,
            "result": self.result.to_dict() if hasattr(self.result, "to_dict") else self.result,
            "error": self.error,
            "processing_time_ms": self.processing_time * 1000,
            "metadata": self.metadata,
        }


@dataclass
class BatchProgress:
    """
    Progress tracking for batch processing.
    
    Attributes:
        total: Total number of items
        completed: Number of completed items
        succeeded: Number of successful items
        failed: Number of failed items
        current_item: Currently processing item ID
    """
    
    total: int
    completed: int = 0
    succeeded: int = 0
    failed: int = 0
    current_item: str | None = None
    start_time: float = field(default_factory=time.time)
    
    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        return (self.completed / self.total * 100) if self.total > 0 else 0
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    @property
    def estimated_remaining(self) -> float | None:
        """Estimate remaining time in seconds."""
        if self.completed == 0:
            return None
        
        rate = self.completed / self.elapsed_time
        remaining_items = self.total - self.completed
        
        return remaining_items / rate if rate > 0 else None
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        return (self.succeeded / self.completed * 100) if self.completed > 0 else 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "completed": self.completed,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "progress_percent": self.progress_percent,
            "elapsed_seconds": self.elapsed_time,
            "estimated_remaining_seconds": self.estimated_remaining,
            "success_rate": self.success_rate,
            "current_item": self.current_item,
        }


# =============================================================================
# Batch Processor
# =============================================================================

class BatchProcessor:
    """
    Efficient batch processor for high-throughput inference.
    
    Features:
        - Parallel preprocessing and inference
        - Priority queue for urgent items
        - Memory-efficient streaming
        - Progress tracking with callbacks
        - Automatic retry with backoff
        - Resource management
    
    Example:
        >>> processor = BatchProcessor(inference_engine)
        >>> 
        >>> items = [
        ...     BatchItem(id="vid1", data=Path("/path/to/video1.mp4")),
        ...     BatchItem(id="vid2", data=Path("/path/to/video2.mp4")),
        ... ]
        >>> 
        >>> for result in processor.process(items):
        ...     print(f"{result.id}: {result.result.prediction}")
    """
    
    def __init__(
        self,
        inference_engine: Any,
        *,
        batch_size: int = 8,
        num_workers: int = 4,
        max_queue_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        progress_callback: Callable[[BatchProgress], None] | None = None,
    ):
        """
        Initialize batch processor.
        
        Args:
            inference_engine: Engine for inference
            batch_size: Number of items to process at once
            num_workers: Number of preprocessing workers
            max_queue_size: Maximum queue size
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay (exponential backoff)
            progress_callback: Callback for progress updates
        """
        self._engine = inference_engine
        self._batch_size = batch_size
        self._num_workers = num_workers
        self._max_queue_size = max_queue_size
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._progress_callback = progress_callback
        
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Processing state
        self._progress = BatchProgress(total=0)
        self._is_processing = False
        self._should_stop = threading.Event()
        
        # Queues
        self._input_queue: queue.PriorityQueue[BatchItem] = queue.PriorityQueue(
            maxsize=max_queue_size
        )
        self._preprocessed_queue: queue.Queue[tuple[str, np.ndarray, dict]] = queue.Queue(
            maxsize=max_queue_size
        )
    
    # =========================================================================
    # Main Processing Methods
    # =========================================================================
    
    def process(
        self,
        items: Sequence[BatchItem] | Iterator[BatchItem],
        *,
        ordered: bool = False,
    ) -> Generator[BatchResult, None, None]:
        """
        Process items and yield results.
        
        Args:
            items: Items to process
            ordered: Whether to yield results in input order
        
        Yields:
            BatchResult for each processed item
        """
        items_list = list(items)
        self._progress = BatchProgress(total=len(items_list))
        self._should_stop.clear()
        self._is_processing = True
        
        self._logger.info(f"Starting batch processing of {len(items_list)} items")
        
        try:
            if ordered:
                yield from self._process_ordered(items_list)
            else:
                yield from self._process_parallel(items_list)
        
        finally:
            self._is_processing = False
            self._logger.info(
                f"Batch processing complete: {self._progress.succeeded} succeeded, "
                f"{self._progress.failed} failed"
            )
    
    def _process_ordered(
        self,
        items: list[BatchItem],
    ) -> Generator[BatchResult, None, None]:
        """Process items maintaining input order."""
        for item in items:
            if self._should_stop.is_set():
                break
            
            self._progress.current_item = item.id
            
            result = self._process_single_item(item)
            
            self._update_progress(result)
            yield result
    
    def _process_parallel(
        self,
        items: list[BatchItem],
    ) -> Generator[BatchResult, None, None]:
        """Process items in parallel (results may be out of order)."""
        with ThreadPoolExecutor(max_workers=self._num_workers) as executor:
            # Submit all items
            futures = {
                executor.submit(self._process_single_item, item): item.id
                for item in items
            }
            
            # Yield results as they complete
            for future in as_completed(futures):
                if self._should_stop.is_set():
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    break
                
                item_id = futures[future]
                
                try:
                    result = future.result()
                except Exception as e:
                    result = BatchResult(
                        id=item_id,
                        success=False,
                        error=str(e),
                    )
                
                self._update_progress(result)
                yield result
    
    def _process_single_item(
        self,
        item: BatchItem,
    ) -> BatchResult:
        """Process a single item with retry logic."""
        start_time = time.time()
        last_error: str | None = None
        
        for attempt in range(self._max_retries + 1):
            try:
                # Load data
                data = self._load_item_data(item)
                
                # Inference
                if isinstance(data, np.ndarray):
                    if data.ndim == 4:  # Video/sequence
                        result = self._engine.predict_sequence(data)
                    else:  # Single image
                        result = self._engine.predict(data)
                else:
                    raise ProcessingError(f"Invalid data type: {type(data)}")
                
                return BatchResult(
                    id=item.id,
                    success=True,
                    result=result,
                    processing_time=time.time() - start_time,
                    metadata=item.metadata,
                )
            
            except Exception as e:
                last_error = str(e)
                
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2 ** attempt)
                    self._logger.warning(
                        f"Retry {attempt + 1}/{self._max_retries} for {item.id}: {e}"
                    )
                    time.sleep(delay)
        
        return BatchResult(
            id=item.id,
            success=False,
            error=last_error,
            processing_time=time.time() - start_time,
            metadata=item.metadata,
        )
    
    def _load_item_data(self, item: BatchItem) -> np.ndarray:
        """Load item data into numpy array."""
        if isinstance(item.data, np.ndarray):
            return item.data
        
        if isinstance(item.data, (str, Path)):
            path = Path(item.data)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            # Import here to avoid circular imports
            from ml.preprocessing.video_processor import VideoProcessor
            
            processor = VideoProcessor()
            
            if path.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
                # Video file
                frames = list(processor.extract_frames(str(path)))
                if not frames:
                    raise ProcessingError(f"No frames extracted from {path}")
                return np.stack([f.frame for f in frames])
            
            else:
                # Image file
                import cv2
                image = cv2.imread(str(path))
                
                if image is None:
                    raise ProcessingError(f"Failed to load image: {path}")
                
                return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        if isinstance(item.data, bytes):
            # Decode bytes
            arr = np.frombuffer(item.data, np.uint8)
            import cv2
            image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ProcessingError("Failed to decode image bytes")
            
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        raise ProcessingError(f"Unsupported data type: {type(item.data)}")
    
    def _update_progress(self, result: BatchResult) -> None:
        """Update progress tracking."""
        self._progress.completed += 1
        
        if result.success:
            self._progress.succeeded += 1
        else:
            self._progress.failed += 1
        
        if self._progress_callback:
            try:
                self._progress_callback(self._progress)
            except Exception as e:
                self._logger.warning(f"Progress callback error: {e}")
    
    # =========================================================================
    # Streaming Processing
    # =========================================================================
    
    def process_stream(
        self,
        item_generator: Iterator[BatchItem],
        *,
        max_concurrent: int = 4,
    ) -> Generator[BatchResult, None, None]:
        """
        Process items from a generator in streaming fashion.
        
        Memory-efficient for large datasets.
        
        Args:
            item_generator: Generator yielding BatchItem objects
            max_concurrent: Maximum concurrent processing
        
        Yields:
            BatchResult for each processed item
        """
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {}
            results_pending = 0
            
            # Process items as they arrive
            for item in item_generator:
                if self._should_stop.is_set():
                    break
                
                # Submit item
                future = executor.submit(self._process_single_item, item)
                futures[future] = item.id
                results_pending += 1
                
                # Check for completed results
                done_futures = [f for f in futures if f.done()]
                
                for future in done_futures:
                    item_id = futures.pop(future)
                    
                    try:
                        result = future.result()
                    except Exception as e:
                        result = BatchResult(
                            id=item_id,
                            success=False,
                            error=str(e),
                        )
                    
                    results_pending -= 1
                    yield result
            
            # Wait for remaining results
            for future in as_completed(futures):
                item_id = futures[future]
                
                try:
                    result = future.result()
                except Exception as e:
                    result = BatchResult(
                        id=item_id,
                        success=False,
                        error=str(e),
                    )
                
                yield result
    
    # =========================================================================
    # Batch Inference
    # =========================================================================
    
    def process_batch(
        self,
        images: Sequence[np.ndarray],
        ids: Sequence[str] | None = None,
    ) -> list[BatchResult]:
        """
        Process a batch of images in a single forward pass.
        
        More efficient for GPU processing.
        
        Args:
            images: List of images
            ids: Optional list of IDs
        
        Returns:
            List of BatchResult
        """
        start_time = time.time()
        
        if ids is None:
            ids = [f"item_{i}" for i in range(len(images))]
        
        if len(ids) != len(images):
            raise ValueError("Number of IDs must match number of images")
        
        try:
            # Batch inference
            results = self._engine.predict_batch(images)
            
            batch_time = time.time() - start_time
            per_item_time = batch_time / len(images)
            
            return [
                BatchResult(
                    id=item_id,
                    success=True,
                    result=result,
                    processing_time=per_item_time,
                )
                for item_id, result in zip(ids, results)
            ]
        
        except Exception as e:
            self._logger.error(f"Batch processing failed: {e}")
            
            return [
                BatchResult(
                    id=item_id,
                    success=False,
                    error=str(e),
                )
                for item_id in ids
            ]
    
    # =========================================================================
    # Control Methods
    # =========================================================================
    
    def stop(self) -> None:
        """Signal processor to stop."""
        self._should_stop.set()
    
    def reset(self) -> None:
        """Reset processor state."""
        self._should_stop.clear()
        self._progress = BatchProgress(total=0)
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def progress(self) -> BatchProgress:
        """Get current progress."""
        return self._progress
    
    @property
    def is_processing(self) -> bool:
        """Check if currently processing."""
        return self._is_processing
    
    @property
    def batch_size(self) -> int:
        """Get batch size."""
        return self._batch_size


# =============================================================================
# Priority Batch Processor
# =============================================================================

class PriorityBatchProcessor(BatchProcessor):
    """
    Batch processor with priority queue support.
    
    Higher priority items are processed first.
    Priority 0 = highest priority.
    """
    
    def add_item(
        self,
        item: BatchItem,
        *,
        block: bool = True,
        timeout: float | None = None,
    ) -> None:
        """
        Add item to processing queue.
        
        Args:
            item: Item to add
            block: Block if queue is full
            timeout: Timeout for blocking
        """
        self._input_queue.put(item, block=block, timeout=timeout)
    
    def add_urgent(
        self,
        item: BatchItem,
    ) -> None:
        """Add item with highest priority."""
        item.priority = 0
        self._input_queue.put(item)
    
    def process_queue(self) -> Generator[BatchResult, None, None]:
        """Process all items in queue."""
        while not self._input_queue.empty():
            if self._should_stop.is_set():
                break
            
            item = self._input_queue.get_nowait()
            result = self._process_single_item(item)
            yield result


# =============================================================================
# Memory-Efficient Batch Iterator
# =============================================================================

class BatchIterator:
    """
    Memory-efficient iterator that yields batches.
    
    Example:
        >>> iterator = BatchIterator(items, batch_size=8)
        >>> for batch in iterator:
        ...     results = process_batch(batch)
    """
    
    def __init__(
        self,
        items: Sequence[Any],
        batch_size: int,
        *,
        drop_last: bool = False,
    ):
        """
        Initialize iterator.
        
        Args:
            items: Items to iterate over
            batch_size: Size of each batch
            drop_last: Drop incomplete final batch
        """
        self._items = items
        self._batch_size = batch_size
        self._drop_last = drop_last
    
    def __iter__(self) -> Generator[list[Any], None, None]:
        """Yield batches."""
        for i in range(0, len(self._items), self._batch_size):
            batch = list(self._items[i:i + self._batch_size])
            
            if self._drop_last and len(batch) < self._batch_size:
                break
            
            yield batch
    
    def __len__(self) -> int:
        """Get number of batches."""
        if self._drop_last:
            return len(self._items) // self._batch_size
        return (len(self._items) + self._batch_size - 1) // self._batch_size
