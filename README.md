# Dynatrace + Red Hat Event Driven Ansible

This collection contains the following Event-Driven Ansible source plugins:

 * dt_webhook - Event-Driven Ansible without simplified event routing (event streams)
 * dt_esa_api

## Auto-Remediation (dt_esa_api)

This Event source plugin from Dynatrace captures all problems from your Dynatrace tenant and in conjunction with Ansible EDA rulebooks helps to enable auto-remediation in your environment.

### Requirements

* Dynatrace SaaS or Managed environment
* Dynatrace API Token with the following scopes: `Read problems` and `Write problems`
* Ansible Automation Platform with EDA Controller instance

### Example rulebook

```yaml
---
- name: Listen for events on a webhook
  hosts: all
  sources:
    - dynatrace.event_driven_ansible.dt_esa_api:
        dt_api_host: "https://abc.live.dynatrace.com"
        dt_api_token: "asjfsjkfjfjh"
        delay: 60 # Default is 60 seconds, i.e. the plugin polls problems every 60 seconds
        proxy: "http://my-proxy:3128" # Proxy through which to access host. (default is none)

  rules:
    - name: Problem payload Dynatrace for CPU issue
      condition: event.title is match("CPU saturation")
      action:
        run_job_template:
          name: "Remediate CPU saturation issue"
          organization: "Default"
    - name: Problem payload Dynatrace for App Failure rate increase issue
      condition: event.title is match("Failure rate increase")
      action:
        run_job_template:
          name: "Remediate Application issue"
          organization: "Default"
    - name: Update comments in Dynatrace
      condition: 
        all: 
          - event.status == "OPEN"
      action:
        run_playbook:
          name: dt-update-comments.yml
```

## dt_webhook - Event-Driven Ansible without simplified event routing (event streams)

The dt_webhook event-source plugin is capable of receiving events from Dynatrace via the "Send event to Event-Driven Ansible" workflow action of the [Red Hat Ansible for Workflows integration](https://docs.dynatrace.com/docs/platform-modules/automations/workflows/actions/red-hat/redhat-even-driven-ansible) **without simplified event routing (event streams)**.

The dt_webhook event-source plugin must be installed within a decision environment on the Event-Driven Ansible Controller.

For more information on how to set up a new decision environment, see [Event-Driven Ansible controller user guide](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/using_automation_decisions/eda-decision-environments).

When **using event streams**, you can use the standard decision environment provided by Red Hat, for example, the [Ansible-rulebook default-de](https://quay.io/repository/ansible/ansible-rulebook?tab=tags&tag=latest). You don't need to build a custom decision environment with the dt_webhook plugin when using event streams.

### Example rulebook

```yaml
---
- name: Listen for events on dt_webhook
  hosts: all
  sources:
    - dynatrace.event_driven_ansible.dt_webhook:
        host: 0.0.0.0
        port: 5000
        token: '{{ <token_variable_name> }}'

  rules:
    - name: API Endpoint not available
      condition: event.payload.eventData["event.name"] is match ("Monitoring not available")
      action:
        run_job_template:
          name: "Trigger test playbook"
          organization: "Default"    
```

## Support 

As Red Hat Ansible Certified Content, this collection is entitled
to support through the Ansible Automation Platform (AAP) using the
**Create issue** button on the top right corner.
If a support case cannot be opened with Red Hat and the collection
has been obtained either from Galaxy or GitHub, there may be community
help available on the [Ansible Forum](https://forum.ansible.com/).

## Licensing

We are using Apache License 2.0 as our default.

### Source Code Headers

Every file containing source code must include copyright and license
information. This includes any JS/CSS files that you might be serving out to
browsers. (This is to help well-intentioned people avoid accidental copying that
doesn't comply with the license.)

Apache header:

    Copyright 2022 Dynatrace LLC

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        https://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

## Additional Questions/Remarks

If you do have additional questions/remarks, feel free to reach out to Dynatrace support (support@dynatrace.com), either via Slack or email.

If you think this template did not solve all your problems, please also let us know, either with a message or a pull request.
Together we can improve this template to make it easier for our future projects.




