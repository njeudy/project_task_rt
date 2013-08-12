# -*- coding: utf-8 -*-

{
    "name": 'project_task_rt',
    "description": u"""
Project Task Request Tracker (project_task_rt)
==============================================

This is a new module that use task inheritance to process requests (issues)
for customer ask or project developpment bug report.

Issue is not a new model but an inherited task that as some new field and 
process incoming email a different way.

A task with a ``support`` tag is a bug report or a customer request by default.
""",
    "version": "0.1",
    "depends": [
        'base',
        'project',
        'project_issue',
    ],
    "author": "Nicolas JEUDY <njeudy@tuxservices.com>",
    "installable" : True,
    "active" : False,
    "data": [
        'data/project_category_record.xml',
    ],
}

