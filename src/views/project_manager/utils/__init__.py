"""
Utilidades para vista completa de proyectos
"""

from .performance_optimizer import (
    PerformanceMonitor,
    WidgetCache,
    LazyLoader,
    MemoryOptimizer,
    RenderOptimizer,
    get_performance_monitor,
    get_widget_cache,
    get_lazy_loader,
    get_memory_optimizer,
    get_render_optimizer
)

from .animations import (
    AnimationManager,
    AnimatedWidget,
    get_animation_manager
)

__all__ = [
    'PerformanceMonitor',
    'WidgetCache',
    'LazyLoader',
    'MemoryOptimizer',
    'RenderOptimizer',
    'get_performance_monitor',
    'get_widget_cache',
    'get_lazy_loader',
    'get_memory_optimizer',
    'get_render_optimizer',
    'AnimationManager',
    'AnimatedWidget',
    'get_animation_manager'
]
