from __future__ import annotations
import sublime
from typing import Tuple
from .types import CompletionItemKind

SublimeKind = Tuple[int, str, str]

# sublime.Kind tuples for sublime.CompletionItem, sublime.QuickPanelItem, sublime.ListInputItem
# https://www.sublimetext.com/docs/api_reference.html#sublime.Kind
KIND_ARRAY = (sublime.KindId.TYPE, "a", "Array")
KIND_BOOLEAN = (sublime.KindId.VARIABLE, "b", "Boolean")
KIND_CLASS = (sublime.KindId.TYPE, "c", "Class")
KIND_COLOR = (sublime.KindId.MARKUP, "c", "Color")
KIND_CONSTANT = (sublime.KindId.VARIABLE, "c", "Constant")
KIND_CONSTRUCTOR = (sublime.KindId.FUNCTION, "c", "Constructor")
KIND_ENUM = (sublime.KindId.TYPE, "e", "Enum")
KIND_ENUMMEMBER = (sublime.KindId.VARIABLE, "e", "Enum Member")
KIND_EVENT = (sublime.KindId.FUNCTION, "e", "Event")
KIND_FIELD = (sublime.KindId.VARIABLE, "f", "Field")
KIND_FILE = (sublime.KindId.NAVIGATION, "f", "File")
KIND_FOLDER = (sublime.KindId.NAVIGATION, "f", "Folder")
KIND_FUNCTION = (sublime.KindId.FUNCTION, "f", "Function")
KIND_INTERFACE = (sublime.KindId.TYPE, "i", "Interface")
KIND_KEY = (sublime.KindId.NAVIGATION, "k", "Key")
KIND_KEYWORD = (sublime.KindId.KEYWORD, "k", "Keyword")
KIND_METHOD = (sublime.KindId.FUNCTION, "m", "Method")
KIND_MODULE = (sublime.KindId.NAMESPACE, "m", "Module")
KIND_NAMESPACE = (sublime.KindId.NAMESPACE, "n", "Namespace")
KIND_NULL = (sublime.KindId.VARIABLE, "n", "Null")
KIND_NUMBER = (sublime.KindId.VARIABLE, "n", "Number")
KIND_OBJECT = (sublime.KindId.TYPE, "o", "Object")
KIND_OPERATOR = (sublime.KindId.KEYWORD, "o", "Operator")
KIND_PACKAGE = (sublime.KindId.NAMESPACE, "p", "Package")
KIND_PROPERTY = (sublime.KindId.VARIABLE, "p", "Property")
KIND_REFERENCE = (sublime.KindId.NAVIGATION, "r", "Reference")
KIND_SNIPPET = (sublime.KindId.SNIPPET, "s", "Snippet")
KIND_STRING = (sublime.KindId.VARIABLE, "s", "String")
KIND_STRUCT = (sublime.KindId.TYPE, "s", "Struct")
KIND_TEXT = (sublime.KindId.MARKUP, "t", "Text")
KIND_TYPEPARAMETER = (sublime.KindId.TYPE, "t", "Type Parameter")
KIND_UNIT = (sublime.KindId.VARIABLE, "u", "Unit")
KIND_VALUE = (sublime.KindId.VARIABLE, "v", "Value")
KIND_VARIABLE = (sublime.KindId.VARIABLE, "v", "Variable")

KIND_ERROR = (sublime.KindId.COLOR_REDISH, "e", "Error")
KIND_WARNING = (sublime.KindId.COLOR_YELLOWISH, "w", "Warning")
KIND_INFORMATION = (sublime.KindId.COLOR_BLUISH, "i", "Information")
KIND_HINT = (sublime.KindId.COLOR_BLUISH, "h", "Hint")

KIND_QUICKFIX = (sublime.KindId.COLOR_YELLOWISH, "f", "QuickFix")
KIND_REFACTOR = (sublime.KindId.COLOR_CYANISH, "r", "Refactor")
KIND_SOURCE = (sublime.KindId.COLOR_PURPLISH, "s", "Source")

COMPLETION_KINDS: dict[CompletionItemKind, SublimeKind] = {
    CompletionItemKind.Text: KIND_TEXT,
    CompletionItemKind.Method: KIND_METHOD,
    CompletionItemKind.Function: KIND_FUNCTION,
    CompletionItemKind.Constructor: KIND_CONSTRUCTOR,
    CompletionItemKind.Field: KIND_FIELD,
    CompletionItemKind.Variable: KIND_VARIABLE,
    CompletionItemKind.Class: KIND_CLASS,
    CompletionItemKind.Interface: KIND_INTERFACE,
    CompletionItemKind.Module: KIND_MODULE,
    CompletionItemKind.Property: KIND_PROPERTY,
    CompletionItemKind.Unit: KIND_UNIT,
    CompletionItemKind.Value: KIND_VALUE,
    CompletionItemKind.Enum: KIND_ENUM,
    CompletionItemKind.Keyword: KIND_KEYWORD,
    CompletionItemKind.Snippet: KIND_SNIPPET,
    CompletionItemKind.Color: KIND_COLOR,
    CompletionItemKind.File: KIND_FILE,
    CompletionItemKind.Reference: KIND_REFERENCE,
    CompletionItemKind.Folder: KIND_FOLDER,
    CompletionItemKind.EnumMember: KIND_ENUMMEMBER,
    CompletionItemKind.Constant: KIND_CONSTANT,
    CompletionItemKind.Struct: KIND_STRUCT,
    CompletionItemKind.Event: KIND_EVENT,
    CompletionItemKind.Operator: KIND_OPERATOR,
    CompletionItemKind.TypeParameter: KIND_TYPEPARAMETER
}

