# ownline-web

### requirements

- **Router** with custom firmware:
    - Like asuswrt-merlin, dd-wrt, openWRT, Tomato, etc
    - **python**:
        - flask
        - paho-mqtt
    - **iptables**:
    - **nginx**:
- **MQTT broker**
- **Domain name** with dynamic record, updated with router IP

### usage

To run development server execute 

````bash
FLASK_APP=. FLASK_ENV=development flask run
````

### Init production DB
Execute `initialize_db_test.py` to create an initial DB with fake services and users.