project_task_rt
===============
Odoo Module that manage bug request and customer support with project.task and tasks types.

I never understand why we need new project_issue model for that ! 
So I implement a proof of concept for my needs with:

- A task has a type now
- A request is a new model that inhérit from project_task and has default fields value (like category, color,) and new field if needed. So you can use tasks fields.

Depends:
========

This module depends on project_task_number

github: https://github.com/njeudy/project_task_number
