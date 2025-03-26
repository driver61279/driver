from typing import Callable, Dict, Optional, TypeVar
import dataclasses
import time


A = TypeVar("A")


@dataclasses.dataclass
class Logger:
    __indent__: int = 0
    __last_log__: str = ""
    __last_indent__: int = 0
    __indent_log_count__: Dict[int, int] = dataclasses.field(default_factory=dict)

    def pre_emit(self) -> None:
        # Overwrite the last log
        if self.__last_log__ != "":
            ll = self.__last_log__
            print(" " * len(ll), end="\r", flush=True)
        if self.__indent__ > 0:
            # Insert newline if needed
            if self.__indent_log_count__[self.__indent__] == 0:
                print()
            # Bump log counter at current indent level
            self.__indent_log_count__[self.__indent__] += 1

    def emit(
        self,
        level: Optional[str],
        msg: str,
        end: str = "\n",
    ) -> None:
        """Emit a hierarchical log string"""
        self.pre_emit()
        # Build the log string with indent levels
        log_str = " │" * self.__indent__ + " "
        if level is not None:
            log_str += f"{level:<4}: {msg}"
        else:
            log_str += msg
        print(log_str, end=end, flush=True)
        self.__last_log__ = log_str if end == "\r" else ""

    def error(self, msg: str) -> None:
        self.emit("Err", msg)

    def warn(self, msg: str) -> None:
        self.emit("Warn", msg)

    def info(self, msg: str, end: str = "\n") -> None:
        self.emit(None, msg, end=end)

    def debug(self, msg: str) -> None:
        return
        # self.emit("Dbg", msg)

    def section(
        self,
        start_msg: str,
        f: Callable[[], A],
        make_end_msg: Optional[Callable[[A], str]] = None,
    ) -> A:
        time = self.timed(start_msg)
        end_msg = ""
        try:
            a = f()
            if make_end_msg is not None:
                end_msg = make_end_msg(a)
            return a
        finally:
            self.end_timed(time, end_msg)

    def timed(self, msg: str) -> float:
        self.emit(None, msg, end="")
        self.__indent__ += 1
        self.__indent_log_count__[self.__indent__] = 0
        return time.time()

    def end_timed(self, start_time: float, msg: str = "") -> None:
        delta = time.time() - start_time
        logs_between = self.__indent_log_count__.pop(self.__indent__)
        self.__indent__ -= 1
        if logs_between == 0:
            self.pre_emit()
            print(f" [{delta:.2f}s] {msg}")
        else:
            self.emit(None, f"└→ [{delta:.2f}s] {msg}")
