def resource_context(resources):
    return "\n".join(f"- {item.name}: {item.description} ({item.uri})" for item in resources)
