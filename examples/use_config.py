from use_nacos import NacosClient

client = NacosClient()

# publish config
client.config.publish("test_config", "DEFAULT_GROUP", "test_value")

# get config
assert client.config.get("test_config", "DEFAULT_GROUP") == "test_value"

# get config with default value
assert client.config.get(
    "test_config_miss", "DEFAULT_GROUP", default="default_value"
) == "default_value"


# subscribe config

def config_update(config):
    print(config)


client.config.subscribe(
    "test_config",
    "DEFAULT_GROUP",
    callback=config_update
)
