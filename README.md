## Dynatrace + Red Hat Event Driven Ansible : Auto-Remediation

This Event source plugin from Dynatrace captures all problems from your Dynatrace tenant and in conjunction with Ansible EDA rulebooks helps to enable auto-remediation in your environment.

## Requirements:
* Dynatrace SaaS or Managed environment
* Dynatrace API Token with the following scopes: `Read problems` and `Write problems`
* Ansible Automation Platform with EDA Controller instance

# Example rulebook
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

If you do have additional questions/remarks, feel free to reach out to Dynatrace support(support@dynatrace.com), either via slack or email.

If you think this template did not solve all your problems, please also let us know, either with a message or a pull request.
Together we can improve this template to make it easier for our future projects.




