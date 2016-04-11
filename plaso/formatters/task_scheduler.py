# -*- coding: utf-8 -*-
"""The Task Scheduler event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class TaskCacheEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Task Scheduler Cache event."""

  DATA_TYPE = u'task_scheduler:task_cache:entry'

  FORMAT_STRING_PIECES = [
      u'Task: {task_name}',
      u'[Identifier: {task_identifier}]']

  FORMAT_STRING_SHORT_PIECES = [
      u'Task: {task_name}']

  SOURCE_LONG = u'Task Cache'
  SOURCE_SHORT = u'REG'


manager.FormattersManager.RegisterFormatter(TaskCacheEventFormatter)
