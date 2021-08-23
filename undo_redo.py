from __future__ import annotations
from typing import List, Callable, Any, Union, Optional


class UndoRedoElement:
    """
    Define Undo-/Redo-Stack-Element by providing functions to call on undo/redo.
    """

    def __init__(self, name, undo_function, redo_function, undo_args=None, redo_args=None):
        self.name: str = name
        self.undo_function: Callable[[Optional[List[Any, ...]]], None] = undo_function
        self.redo_function: Callable[[Optional[List[Any, ...]]], None] = redo_function
        self.undo_args: Optional[List[Any, ...]] = undo_args
        self.redo_args: Optional[List[Any, ...]] = redo_args

    def on_undo(self) -> None:
        if self.undo_args:
            self.undo_function(*self.undo_args)
            return
        self.undo_function()

    def on_redo(self) -> None:
        if self.redo_args:
            self.redo_function(*self.redo_args)
            return
        self.redo_function(*self.redo_args)


class UndoRedoStack:
    """
    Simple undo redo functionality. Invalidate redo buffer on overwrite.
    """

    def __init__(self, max_size: int):
        self.stack: List[UndoRedoElement] = list()
        self.max_size: int = max_size
        self.undo_top: int = 0
        self.redo_top: int = 0
        self.stack_bottom: int = 0
        self.undo_is_empty: bool = True
        self.redo_is_empty: bool = True

    def __next_index(self) -> int:
        """
        Return next index.
        """
        return (self.undo_top + 1) % self.max_size

    def __prev_index(self) -> int:
        """
        Return previous index.
        """
        return (self.undo_top - 1) % self.max_size

    def undo(self) -> None:
        """
        Undo the last operation on the stack.
        """
        if self.undo_is_empty:
            return

        # Undo last action and mark redo as not empty.
        self.stack[self.undo_top].on_undo()
        self.redo_is_empty = False

        # Mark undo-stack as empty when bottom is undone.
        if self.undo_top == self.stack_bottom:
            self.undo_is_empty = True
            return

        # Move undo pointer down.
        self.undo_top = self.__prev_index()

    def redo(self) -> None:
        """
        Redo the next operation on the stack.
        """
        if self.redo_is_empty:
            return

        # Redo last action.
        index = self.__next_index()
        self.stack[index].on_redo()
        self.undo_top = index

        # Mark redo-stack as empty when top is reached.
        if self.undo_top == self.redo_top:
            self.redo_is_empty = True

    def add_create_element(self, name, undo_function, redo_function, undo_args=None, redo_args=None) -> None:
        """
        Create Undo-/Redo-Element and add it to the stack.
        """
        self.add_element(
            UndoRedoElement(
                name,
                undo_function,
                redo_function,
                undo_args,
                redo_args)
        )

    def add_element(self, element: UndoRedoElement) -> None:
        """
        Add one Undo-/Redo-Element to the Stack.
        """
        # Get index to add the element at.
        index = self.__next_index()
        if self.undo_is_empty:
            index = self.stack_bottom

        # If the index is available, we overwrite the element stored at index.
        # When max capacity is reached, the stack bottom is moved up.
        # In case redo_top is passed, move it up too.
        if index < len(self.stack):
            self.stack[index] = element
            if self.stack_bottom == index:
                self.stack_bottom = (self.stack_bottom + 1) % self.max_size

        # If index is out of range and not at max capacity, append
        # the new element and move undo_top and redo_top up.
        else:
            self.stack.append(element)

        # Update pointers and make sure undo-stack is not marked as empty after
        # adding new element.
        self.undo_top = index
        self.redo_top = index
        self.undo_is_empty = False

    def __repr__(self) -> str:
        """
        Return current status as string.
        """
        msg = f"Max size:  {self.max_size}\n"
        msg += f"Current size: {len(self.stack)}\n"
        msg += f"Bottom: {self.stack_bottom}\n"
        msg += f"Undo: {self.undo_top}\nRedo: {self.redo_top}\n"
        msg += f"Undo empty: {self.undo_is_empty}\n"
        msg += f"Redo empty: {self.redo_is_empty}"
        return msg
