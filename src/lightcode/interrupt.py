"""Interrupt handling for user-requested interruptions."""

import os
import signal
import sys
import threading
from contextlib import contextmanager
from typing import Generator


class InterruptRequested(Exception):
    """Exception raised when user requests interruption."""

    pass


class EscKeyMonitor:
    """Background thread that monitors for Esc key presses using /dev/tty.

    This monitor runs continuously and does not exit when Esc is detected.
    It simply sets the interrupt flag and continues monitoring.
    """

    def __init__(self, handler: "InterruptHandler"):
        self._handler = handler
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._tty_fd: int | None = None
        self._started = False

    def start(self) -> None:
        """Start monitoring for Esc key in background thread."""
        if self._started:
            return  # Already running

        if sys.platform == "win32":
            self._thread = threading.Thread(target=self._monitor_windows, daemon=True)
        else:
            # Unix: open /dev/tty directly to avoid conflicts with stdin
            try:
                self._tty_fd = os.open("/dev/tty", os.O_RDONLY)
            except OSError:
                # No TTY available
                return
            self._thread = threading.Thread(target=self._monitor_unix, daemon=True)

        self._stop_event.clear()
        self._started = True
        self._thread.start()

    def stop(self) -> None:
        """Stop monitoring."""
        if not self._started:
            return

        self._stop_event.set()
        # Wait for thread to finish before closing fd
        if self._thread is not None:
            self._thread.join(timeout=0.5)
            self._thread = None
        if self._tty_fd is not None:
            try:
                os.close(self._tty_fd)
            except OSError:
                pass
            self._tty_fd = None
        self._started = False

    def _monitor_unix(self) -> None:
        """Monitor for Esc key on Unix using /dev/tty."""
        import select
        import termios

        # Copy fd to local variable to avoid race condition with stop()
        fd = self._tty_fd
        if fd is None:
            return

        # Save terminal settings and configure for raw input
        try:
            old_settings = termios.tcgetattr(fd)
            new_settings = termios.tcgetattr(fd)
            # Disable canonical mode (ICANON) and echo (ECHO)
            # This allows reading individual characters without waiting for newline
            new_settings[3] = new_settings[3] & ~(termios.ICANON | termios.ECHO)
            # Set VMIN=0, VTIME=0 for non-blocking read
            new_settings[6][termios.VMIN] = 0
            new_settings[6][termios.VTIME] = 0
            termios.tcsetattr(fd, termios.TCSANOW, new_settings)
        except (termios.error, OSError):
            return

        try:
            while not self._stop_event.is_set():
                # Use select with timeout for responsive stopping
                try:
                    rlist, _, _ = select.select([fd], [], [], 0.1)
                    if rlist:
                        ch = os.read(fd, 1)
                        if ch == b"\x1b":  # Esc
                            self._handler.request_interrupt()
                            # Don't break - continue monitoring
                except (OSError, ValueError):
                    break
        finally:
            # Restore terminal settings
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except (termios.error, OSError):
                pass

    def _monitor_windows(self) -> None:
        """Monitor for Esc key on Windows."""
        import msvcrt

        while not self._stop_event.is_set():
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch == b"\x1b":  # Esc
                    self._handler.request_interrupt()
                    # Don't break - continue monitoring
            self._stop_event.wait(0.1)


def run_with_interrupt(
    func,
    handler: "InterruptHandler",
    check_interval: float = 0.1,
):
    """Run function with interrupt support.

    Runs the given function in a background thread while monitoring for
    interrupts. The caller should have already called handler.monitor_keys().

    Args:
        func: The function to run
        handler: Interrupt handler for coordination
        check_interval: How often to check for interrupts (seconds)

    Returns:
        The result of the function

    Raises:
        InterruptRequested: If user requests interruption
        Exception: Any exception raised by the function
    """
    result_container: dict = {"result": None, "error": None}
    done = threading.Event()

    def worker():
        try:
            result_container["result"] = func()
        except Exception as e:
            result_container["error"] = e
        finally:
            done.set()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    # Wait for completion while checking for interrupts
    while not done.is_set():
        if handler.is_interrupted():
            raise InterruptRequested()
        done.wait(timeout=check_interval)

    if result_container["error"]:
        raise result_container["error"]

    return result_container["result"]


class InterruptHandler:
    """Handles interrupt requests from Ctrl-C and Esc key."""

    def __init__(self):
        self._interrupted = threading.Event()
        self._original_handler = None
        self._esc_monitor: EscKeyMonitor | None = None
        self._monitoring = False

    def request_interrupt(self) -> None:
        """Signal that an interrupt has been requested."""
        self._interrupted.set()

    def is_interrupted(self) -> bool:
        """Check if an interrupt has been requested."""
        return self._interrupted.is_set()

    def reset(self) -> None:
        """Reset the interrupt state."""
        self._interrupted.clear()

    def check_and_raise(self) -> None:
        """Check for interrupt and raise if requested."""
        if self._interrupted.is_set():
            raise InterruptRequested()

    def start_monitoring(self) -> None:
        """Start monitoring for Ctrl-C and Esc key.

        Call this once at the start of the REPL loop.
        """
        if self._monitoring:
            return

        # Install SIGINT handler
        def sigint_handler(signum, frame):
            self.request_interrupt()

        self._original_handler = signal.signal(signal.SIGINT, sigint_handler)

        # Start Esc key monitor
        self._esc_monitor = EscKeyMonitor(self)
        self._esc_monitor.start()

        self._monitoring = True

    def stop_monitoring(self) -> None:
        """Stop monitoring for Ctrl-C and Esc key.

        Call this when exiting the REPL loop.
        """
        if not self._monitoring:
            return

        # Stop Esc key monitor
        if self._esc_monitor:
            self._esc_monitor.stop()
            self._esc_monitor = None

        # Restore SIGINT handler
        if self._original_handler is not None:
            signal.signal(signal.SIGINT, self._original_handler)
            self._original_handler = None

        self._monitoring = False

    @contextmanager
    def monitoring(self) -> Generator[None, None, None]:
        """Context manager to monitor both Ctrl-C and Esc key."""
        self.start_monitoring()
        try:
            yield
        finally:
            self.stop_monitoring()
