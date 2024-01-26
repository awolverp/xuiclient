# XUIClient
A rich-feature and easy-to-use Python library to control your XUI-Panel.

> [!WARNING]
> This package is outdated and does not support the new updates of XUI panels and XRay cores. Maybe some APIs have been changed.

**features**:
- Very fast
- Very easy to use
- Supported all of protocols such as **VMess**, **VLess**, **Shadowsocks**, **Dokodemo-door**, ...
- Supported all of transmissions such as **tcp**, **kcp**, **ws**, ...

**Content**:
- [Install](#install)
- [Simple Example](#simple-example)
- [Usage](#usage)
    - [Methods](#methods)
    - [How to get protocols link](#how-to-get-protocols-link)

### Simple example
```python
from xuiclient import Client, types, protocols

cli = Client("http://127.0.0.1:54321", cookie_file=".cookie")

cli.login("admin", "admin")

id = cli.add_inbound(
    protocols.VMessProtocol(
        remark="NAME",
        total_traffic=types.GIGABYTE*10, # 10G
    )
)

for p in cli.get_all_inbounds():
    print(p)
```

## Usage
First create Client and login:

> We use '127.0.0.1:54321' for server address in this example.

```python
from xuiclient import Client

cli = Client("http://127.0.0.1:54321", cookie_file=".cookie")
cli.login("username", "password")
```

**What is cookie_file parameter?** If you set this parameter, the client will save session cookie into that
to prevent logging again. with this, you don't need to logout.

### Methods
Now you can control your panel. we have 15 functions for this:

#### get_status
Returns your server status.

```python
status = cli.get_status()
print(status)
# Status(cpu=10.012515644560525, mem=StatusInfo(current=1708163072, total=4011470848), ...)
```

#### get_settings
Returns settings information.

```python
settings = cli.get_settings()
print(settings)
```

#### get_lastest_xray_version
Returns latest XRay service version.

```python
version = cli.get_lastest_xray_version()
print(version)
# 6.0.0
```

#### is_xray_latest_version
Returns `True` if your xray version is latest.

```python
ok = cli.is_xray_latest_version()
print(ok)
```

#### install_new_xray_service
Installs new XRay service.

```python
cli.install_new_xray_service("6.0.0")
```

#### update_settings
Updates settings.

*Recommend to use `get_settings()` and use `Settings` type to update settings.


```python
setting = cli.get_settings()
# your changes
cli.update_settings(setting)
```

#### update_user
Updates username and password.

*After update, it tries to logout and login with new username and password to avoid some problems.

```python
cli.update_user("username", "password", "newuser", "newpass")
```

#### get_email_ips
Returns IPs of an email.

```python
print(cli.get_email_ips("awolverp@gmail.com"))
# ["92.32.32.9", ...]
```

#### clear_email_ips
Clears IPs of an email.

```python
cli.clear_email_ips("awolverp@gmail.com")
```

#### get_all_inbounds
Returns all inbounds.

```python
for p in cli.get_all_inbounds():
    print(p)
# xuiclient.protocols.VMessProtocol(id=1, remark='NAME', enabled=True)
# ...
```

#### get_inbound
*Only 'NidukaAkalanka/x-ui-english' supported this.

Returns the inbound which has specified id.

Returns `None` if not exists.

```python
print(cli.get_inbound(1))
# xuiclient.protocols.VMessProtocol(id=1, remark='NAME', enabled=True)
```

#### delete_inbound
Deletes inbound which has specified id.

```python
cli.delete_inbound(1)
```

#### add_inbound
Adds new inbound and returns id of that.

> ⚠️ **Always try to set all parameters of protocols** to prevent x-ui panels errors.

```python
from xuiclient import protocols, types
from datetime import datetime, timedelta

cli.add_inbound(
    protocols.VLessProtocol(
        remark="TEST",
        port=12345,
        expiry_time=datetime.now()+timedelta(days=30), # 30 days
        total_traffic=100*types.GIGABYTE, # 100GiB
        transmission=protocols.WSTransmission(),
        tls=protocols.XTLS(),
        clients=[protocols.ProtocolClient(email="awolverp@gmail.com")],
    )
)
```

#### add_inbounds_many
Shorthand for `for p in protocols: cli.add_inbound(p)`.

```python
from xuiclient import protocols

cli.add_inbounds_many(
    protocols.VLessProtocol(
        remark="TEST",
        port=12345
    ),
    protocols.SocksProtocol(
        remark="TEST",
        port=12346
    ),
    protocols.DokodemoDoor(
        remark="TEST",
        port=12347
    )
)
```

#### update_inbound
Changes one inbound which has specified id to another that you specified.

```python
cli.update_inbound(
    1,
    protocols.VLessProtocol(
        remark="TEST",
        port=12345
    ),
)
```

### How to get protocols link?
use `generate_access_link` method.
example:

```python
for p in cli.get_all_inbounds():
    print(p.generate_access_link(cli.hostname))

# Or create manually:

p = protocols.VMessProtocol(
    remark="NAME", port=10382,
)
print(p.generate_access_link(cli.hostname))
```

Or if you have multi-user protocol and want to generate link for each user, can follow this way:
```python
for p in cli.get_all_inbounds():
    
    try:
        clients_len = len(p.clients)
    except AttributeError:
        # some protocols not supported multi-user
        print(p.generate_access_link(cli.hostname))
    
    else:
        for i in range(clients_len):
            print(p.generate_access_link(cli.hostname, client_index=i))
```
