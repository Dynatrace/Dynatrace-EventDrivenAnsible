## Dynatrace + Red Hat Event Driven Ansible : Auto-Remediation

This Event source plugin from Dynatrace captures all problems from your Dynatrace tenant and in conjunction with Ansible EDA rulebooks helps to enable auto-remediation in your environment.

## Requirements:
* Dynatrace SaaS or Managed environment
* Dynatrace API Token with the following permissions: `Read configuration`, `Write configuration`, `Access problem and event feed, metrics, and topology`
* Ansible Automation Platform with Controller instance
* Ansible EDA controller where this plugin will be installed within the Dynatrace collection
* GitHub repository forked from this repository

# rulebook
  sources:
    - dynatrace.eda.dt_esa_api:
        dt_api_host:     # Dynatrace hostname to listen to
        dt_api_token:    # API token

# Examples

---
- name: Listen for events on a webhook
  hosts: all
  sources:
    - dynatrace.eda.dt_esa_api:
        dt_api_host: "https://abc.live.dynatrace.com" or "https://abc.apps.dynatrace.com"
        dt_api_token: "asjfsjkfjfjh"
        delay: 60 (Default is 1 min) i.e plugin runs every 1 minute

  rules:
    - name: Problem payload Dynatrace for CPU issue
      condition: event.payload.problemTitle contains "CPU saturation"
      action:
        run_job_template:
          name: "Remediate CPU saturation issue"
          organization: "Default"
    - name: Problem payload Dynatrace for App Failure rate increase issue
      condition: event.payload.problemTitle contains "Failure rate increase"
      action:
        run_playbook:
          name: "Remediate Application issue"
          organization: "Default

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

# rulebook
  sources:
    - dynatrace.eda.dt_esa_api:
        dt_api_host:     # Dynatrace hostname to listen to
        dt_api_token:    # API token

## Additional Questions/Remarks

If you do have additional questions/remarks, feel free to reach out to OSPO, either via slack or email.

If you think this template did not solve all your problems, please also let us know, either with a message or a pull request.
Together we can improve this template to make it easier for our future projects.




