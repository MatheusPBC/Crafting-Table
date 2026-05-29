import fs from "fs"
import path from "path"
import { tool } from "@opencode-ai/plugin"

const CONFIG_DIR = "/home/matheus/.config/opencode"

function countEntries(dir, predicate) {
  if (!fs.existsSync(dir)) return 0
  return fs.readdirSync(dir, { withFileTypes: true }).filter(predicate).length
}

export default tool({
  description: "Summarize the globally available OpenCode setup: agents, commands, skills, tools, and config path.",
  args: {},
  async execute() {
    const skills = countEntries(path.join(CONFIG_DIR, "skills"), (e) => e.isDirectory())
    const agents = countEntries(path.join(CONFIG_DIR, "agents"), (e) => e.isFile() && e.name.endsWith('.md'))
    const commands = countEntries(path.join(CONFIG_DIR, "commands"), (e) => e.isFile() && e.name.endsWith('.md'))
    const tools = countEntries(path.join(CONFIG_DIR, "tools"), (e) => e.isFile() && (e.name.endsWith('.js') || e.name.endsWith('.ts')))

    return [
      'Global OpenCode context:',
      `- Config: ${path.join(CONFIG_DIR, 'opencode.json')}`,
      `- Agents: ${agents}`,
      `- Commands: ${commands}`,
      `- Skills: ${skills}`,
      `- Custom tools: ${tools}`,
    ].join('\n')
  },
})
