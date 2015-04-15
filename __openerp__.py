# -*- coding: utf-8 -*-

{
    "name": 'project_task_rt',
    "description": u"""
Project Task Request Tracker (project_task_rt)
==============================================

This is a new module that use task inheritance to process requests (issues)
for customer ask or project developpment bug report.

Issue is not a new model but an inherited task that as some new field and
process incoming email a different way. the new model project.task.rt is an
Abstract class to only have a hook form incoming email and set default task value

A task with a ``support`` tag is a bug report or a customer request by default.

This module add an new subtype field for task to handle different type of task.

External dependecies
--------------------

- project_task_number: Add a ``ref`` fields.sequence to task

""",
    "version": "0.1",
    "depends": [
        'base',
        'project',
        'web_widget_text_markdown',
        'project_timesheet',
        'project_task_number',
    ],
    "author": "Nicolas JEUDY <njeudy@tuxservices.com>",
    "installable" : True,
    "active" : False,
    "data": [
        'data/project_category_record.xml',
        'ir_ui_view_record.xml',
        'ir_actions_act_window_record.xml',
        'ir_actions_act_window_view_record.xml',
        'ir_ui_menu_record.xml',
        'security/request_security.xml',
        'security/ir.model.access.csv',
    ],
}

