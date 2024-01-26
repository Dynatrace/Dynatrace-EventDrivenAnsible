# Event-source plugin dt_webhook

The dt_webhook event-source plugin is capable of receiving events (from Dynatrace) via a webhook and is extended with token based authentication.

## Run unit/integration tests

 * In order to run the unit/integration tests you need to install `pytest`
 ```
 pip install pytest
 ```
 * Unit tests are located in `/tests/unit/test_dt_webhook.py`
 * Integration tests are located in `/tests/integration/test_dt_webhook.py`
 * Run the following command to execute the tests
 ```
 pytest tests/unit/test_dt_webhook.py
 ```

## Test dt_webhook locally with ansible-rulebook

### Python requirements

 * Python >= 3.9
 * pip 

### Pre-requisites 

Install:

* Python 3.9

```
#install python version 3.9.X
apt-get install python3.9 
```

 *  pip - package installer for python. 
     * Easiest way to install is to use the get-pi.py bootstrapping script from PyPa

```
curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.9 get-pip.py
```

 * ansible-core
 * ansible-rulebook 

```
pip3.9 install ansible ansible-runner ansible-rulebook
```

*Remark: Run pip3.9 to ensure that python version 3.9 is used. You only get the latest ansible-rulebook version with python version >= 3.9*

**Optional:**

 * ansible collection(s):
     * ansible.eda

## How-to test it locally (without EDA controller)

The following resources for local tests are needed:

* an example rulebook called `dt_event_example_rule.yml` in `/rulebooks`
* an example playbook called `run_task.yml` in `/playbooks`
* an example event called `example_event.json` in `/playbooks`

Steps to do:

* Checkout the GitHub repository

* Create a vars.yml file in the rulebooks directory and configure the variable var_eda_token. This “token variable” will then be used when running the rulebook and passed to the event-source plugin. Hint: Currently the token configuration is done by setting a variable. This will be changed in the future.

```
var_eda_token: <your-test-token> 
```

 * Go to your terminal and run the example rulebook with the following command

```
ansible-rulebook --rulebook rulebooks/dt_event_example_rule.yml -e rulebooks/vars.yml -i inventory.yml -S extensions/eda/plugins/event_source/
```

 * Executing the command above should start the rulebook. The rulebook will listen to the port which is configured in the rulebook itself like in this case

```
# use the source name dt_webhook for local tests
# use the FQCN dynatrace.event_driven_ansible.dt_webhook in PRODUCTION 
  sources:
    - dt_webhook:
        host: localhost
        port: 1234
        token: '{{ var_eda_token }}' 
```

 * When the rulebook is running you can send a the following curl request to trigger the rulebook from another terminal

```
curl -X POST --header "Authorization: Bearer <your-test-token>" --data '{
  "eventData": {
    "affected_entity_ids": ["KUBERNETES_CLUSTER-123456789"],
    "event.category": "AVAILABILITY",
    "event.name": "Monitoring not available",
    "event.status": "ACTIVE"
  }
}' localhost:1234/event
```

 * If it works you should see the following output of the rulebook

```
PLAY [local event-driven-ansible test] *****************************************

TASK [Gathering Facts] *********************************************************
ok: [localhost]

TASK [Print Dynatrace event] ***************************************************
ok: [localhost] => {
    "msg": {
        "eventData": {
            "affected_entity_ids": [
                "KUBERNETES_CLUSTER-123456789"
            ],
            "event.category": "AVAILABILITY",
            "event.name": "Monitoring not available",
            "event.status": "ACTIVE"
        }
    }
}

TASK [Here could be your ansible task for resolving the problem] ***************
ok: [localhost] => {
    "msg": "Resolve problem for the following affected entities ['KUBERNETES_CLUSTER-123456789']"
}

PLAY RECAP *********************************************************************
localhost                  : ok=3    changed=0    unreachable=0    failed=0    skipped=0    resc
```