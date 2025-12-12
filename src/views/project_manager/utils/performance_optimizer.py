"""
Utilidades de optimización de rendimiento para vista completa

Proporciona herramientas para mejorar el rendimiento en proyectos
con gran cantidad de items:
- Lazy loading de items
- Caché de widgets
- Limpieza de memoria
- Monitoreo de rendimiento

Autor: Widget Sidebar Team
Versión: 1.0
"""

import time
from typing import Dict, List, Optional
from PyQt6.QtCore import QTimer
from functools import lru_cache


class PerformanceMonitor:
    """
    Monitor de rendimiento para operaciones de renderizado

    Registra tiempos de ejecución y proporciona métricas
    de rendimiento para identificar cuellos de botella.
    """

    def __init__(self):
        self.metrics = {}

    def start_timer(self, operation: str):
        """Iniciar timer para una operación"""
        self.metrics[operation] = {'start': time.time()}

    def end_timer(self, operation: str):
        """Finalizar timer y calcular duración"""
        if operation in self.metrics:
            start_time = self.metrics[operation]['start']
            duration = time.time() - start_time
            self.metrics[operation]['duration'] = duration
            return duration
        return 0

    def get_metric(self, operation: str) -> Optional[float]:
        """Obtener métrica de una operación"""
        if operation in self.metrics and 'duration' in self.metrics[operation]:
            return self.metrics[operation]['duration']
        return None

    def get_all_metrics(self) -> Dict[str, float]:
        """Obtener todas las métricas"""
        return {
            op: data.get('duration', 0)
            for op, data in self.metrics.items()
        }

    def print_report(self):
        """Imprimir reporte de rendimiento"""
        print("\n" + "=" * 60)
        print("REPORTE DE RENDIMIENTO")
        print("=" * 60)

        for operation, data in self.metrics.items():
            duration = data.get('duration', 0)
            print(f"{operation:.<40} {duration:.3f}s")

        print("=" * 60 + "\n")


class WidgetCache:
    """
    Caché de widgets reutilizables

    Almacena widgets creados previamente para reutilización,
    reduciendo overhead de creación de widgets PyQt6.
    """

    def __init__(self, max_size: int = 100):
        """
        Inicializar caché

        Args:
            max_size: Tamaño máximo del caché
        """
        self.max_size = max_size
        self.cache = {}
        self.usage_count = {}

    def get(self, key: str):
        """
        Obtener widget del caché

        Args:
            key: Clave del widget

        Returns:
            Widget si existe, None en caso contrario
        """
        if key in self.cache:
            self.usage_count[key] = self.usage_count.get(key, 0) + 1
            return self.cache[key]
        return None

    def put(self, key: str, widget):
        """
        Agregar widget al caché

        Args:
            key: Clave del widget
            widget: Widget a almacenar
        """
        # Si el caché está lleno, eliminar el menos usado
        if len(self.cache) >= self.max_size:
            least_used = min(self.usage_count.items(), key=lambda x: x[1])
            self.remove(least_used[0])

        self.cache[key] = widget
        self.usage_count[key] = 0

    def remove(self, key: str):
        """Eliminar widget del caché"""
        if key in self.cache:
            widget = self.cache[key]
            if hasattr(widget, 'deleteLater'):
                widget.deleteLater()
            del self.cache[key]
            if key in self.usage_count:
                del self.usage_count[key]

    def clear(self):
        """Limpiar todo el caché"""
        for widget in self.cache.values():
            if hasattr(widget, 'deleteLater'):
                widget.deleteLater()
        self.cache.clear()
        self.usage_count.clear()

    def get_size(self) -> int:
        """Obtener tamaño actual del caché"""
        return len(self.cache)

    def get_hit_rate(self) -> float:
        """Calcular tasa de aciertos del caché"""
        total_usage = sum(self.usage_count.values())
        if total_usage == 0:
            return 0.0
        hits = sum(1 for count in self.usage_count.values() if count > 0)
        return hits / len(self.usage_count) if self.usage_count else 0.0


class LazyLoader:
    """
    Cargador lazy de items

    Carga items bajo demanda en lugar de cargar todo el proyecto
    de una vez, mejorando tiempo de carga inicial.
    """

    def __init__(self, batch_size: int = 20):
        """
        Inicializar lazy loader

        Args:
            batch_size: Cantidad de items a cargar por lote
        """
        self.batch_size = batch_size
        self.loaded_items = set()

    def should_load(self, item_id: int) -> bool:
        """
        Verificar si un item debe ser cargado

        Args:
            item_id: ID del item

        Returns:
            True si debe cargarse, False si ya está cargado
        """
        return item_id not in self.loaded_items

    def mark_loaded(self, item_id: int):
        """Marcar item como cargado"""
        self.loaded_items.add(item_id)

    def get_next_batch(self, all_items: List[Dict]) -> List[Dict]:
        """
        Obtener siguiente lote de items a cargar

        Args:
            all_items: Lista completa de items

        Returns:
            Lista con el siguiente lote de items
        """
        unloaded = [
            item for item in all_items
            if item['id'] not in self.loaded_items
        ]

        batch = unloaded[:self.batch_size]

        for item in batch:
            self.loaded_items.add(item['id'])

        return batch

    def reset(self):
        """Resetear estado del loader"""
        self.loaded_items.clear()

    def get_loaded_count(self) -> int:
        """Obtener cantidad de items cargados"""
        return len(self.loaded_items)


class MemoryOptimizer:
    """
    Optimizador de memoria

    Limpia widgets no visibles y libera memoria no utilizada.
    """

    @staticmethod
    def cleanup_widget(widget):
        """
        Limpiar widget y sus hijos

        Args:
            widget: Widget a limpiar
        """
        if not widget:
            return

        # Limpiar hijos recursivamente
        for child in widget.findChildren(object):
            if hasattr(child, 'deleteLater'):
                child.deleteLater()

        # Limpiar el widget principal
        if hasattr(widget, 'deleteLater'):
            widget.deleteLater()

    @staticmethod
    def cleanup_layout(layout):
        """
        Limpiar todos los widgets de un layout

        Args:
            layout: Layout a limpiar
        """
        if not layout:
            return

        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                MemoryOptimizer.cleanup_widget(child.widget())
            elif child.layout():
                MemoryOptimizer.cleanup_layout(child.layout())


class RenderOptimizer:
    """
    Optimizador de renderizado

    Proporciona estrategias para optimizar el renderizado
    de grandes cantidades de items.
    """

    def __init__(self):
        self.render_queue = []
        self.render_timer = None

    def schedule_render(self, callback, delay_ms: int = 100):
        """
        Programar renderizado con delay

        Args:
            callback: Función a ejecutar
            delay_ms: Delay en milisegundos
        """
        if self.render_timer:
            self.render_timer.stop()

        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(callback)
        self.render_timer.start(delay_ms)

    def batch_render(self, items: List, render_func, batch_size: int = 10):
        """
        Renderizar items en lotes

        Args:
            items: Lista de items a renderizar
            render_func: Función de renderizado
            batch_size: Tamaño del lote
        """
        self.render_queue = items.copy()

        def render_next_batch():
            if not self.render_queue:
                return

            batch = self.render_queue[:batch_size]
            self.render_queue = self.render_queue[batch_size:]

            for item in batch:
                render_func(item)

            if self.render_queue:
                QTimer.singleShot(50, render_next_batch)

        render_next_batch()


# Singleton para uso global
_performance_monitor = PerformanceMonitor()
_widget_cache = WidgetCache()
_lazy_loader = LazyLoader()
_memory_optimizer = MemoryOptimizer()
_render_optimizer = RenderOptimizer()


def get_performance_monitor() -> PerformanceMonitor:
    """Obtener instancia global del monitor de rendimiento"""
    return _performance_monitor


def get_widget_cache() -> WidgetCache:
    """Obtener instancia global del caché de widgets"""
    return _widget_cache


def get_lazy_loader() -> LazyLoader:
    """Obtener instancia global del lazy loader"""
    return _lazy_loader


def get_memory_optimizer() -> MemoryOptimizer:
    """Obtener instancia global del optimizador de memoria"""
    return _memory_optimizer


def get_render_optimizer() -> RenderOptimizer:
    """Obtener instancia global del optimizador de renderizado"""
    return _render_optimizer
