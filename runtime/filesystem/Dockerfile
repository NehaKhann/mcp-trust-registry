# The REAL, official MCP reference server for filesystem access -
# published by the Model Context Protocol maintainers, not written by us.
#
# Network access is needed here at BUILD time to install it from npm.
# It is deliberately NOT needed (and blocked) at RUN time - that split is
# the whole point: by the time we run this image for a scan, `docker run
# --network none` means the server has zero path to exfiltrate anything
# even if it wanted to, regardless of what its code does.
FROM node:20-slim

RUN npm install -g @modelcontextprotocol/server-filesystem

ENTRYPOINT ["mcp-server-filesystem"]
