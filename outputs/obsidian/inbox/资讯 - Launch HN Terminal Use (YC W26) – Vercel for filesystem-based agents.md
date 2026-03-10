# 资讯 - Launch HN Terminal Use (YC W26) – Vercel for filesystem-based agents

关联：[[AI Radar 日报 - 2026-03-10 - 20260310_032327]] | [[结果索引]] | [[任务笔记 - AI Radar 搭建]]

## 结论与建议
- 推荐级别：重点关注
- 总分：7.9
- 关注建议：建议加入观察清单，今天至少完成一次快速复盘。
- 评分理由：总分 7.9。个人相关性较强（9.1）；新颖性较强（8.7）。

## 基本信息
- 来源：hackernews
- 标题：Launch HN: Terminal Use (YC W26) – Vercel for filesystem-based agents
- 链接：https://news.ycombinator.com/item?id=47311657
- 时间：2026-03-09T16:53:52+00:00
- 作者 / 维护者：filipbalucha
- 使用模型：mistral:7b
- HN 分数：40
- HN 评论数：20

## 标签
- Hacker News
- Agent
- 大模型
- 开发工具
- 自动化

## 分数拆解
- 新颖性：8.7
- 落地信号：5.6
- 个人相关性：9.1

## 中文总结
### 内容概述
Terminal Use 是一个新项目，旨在简化在沙箱环境中运行需要文件系统的代理（agent）的部署。这包括编码代理、研究代理、文档处理代理和读写文件的内部工具。

### 解决的问题
Terminal Use 解决了在部署代理时需要组合多个部分的问题，包括代理打包、在沙箱中运行代理、向用户发送消息、持久化状态以及文件与代理工作区之间的管理。

### 为什么值得关注
Terminal Use 提供了一个简单的方法来从存储库中打包代理代码，并通过 API/SDK 服务它。它还提供了一个文件系统 SDK，使用户可以直接上传和下载文件，而无需通过后端代理文件传输。

### 适合我关注的原因
作为个人 AI 情报系统使用者，Terminal Use 可以帮助我更容易地部署和管理在沙箱环境中运行的代理，并提供了一个方便的文件系统 SDK 来管理文件。

### 关键词
- Terminal Use
- 代理
- 文件系统
- 沙箱
- API
- SDK
- 部署
- 管理

### 简洁引用
> “We built Terminal Use to make it easier to deploy agents that work in a sandboxed environment and need filesystems to do work.”

## 原始内容
标题：Launch HN: Terminal Use (YC W26) – Vercel for filesystem-based agents
文本：Hello Hacker News! We&#x27;re Filip, Stavros, and Vivek from Terminal Use (<a href="https:&#x2F;&#x2F;www.terminaluse.com&#x2F;">https:&#x2F;&#x2F;www.terminaluse.com&#x2F;</a>). We built Terminal Use to make it easier to deploy agents that work in a sandboxed environment and need filesystems to do work. This includes coding agents, research agents, document processing agents, and internal tools that read and write files.<p>Here&#x27;s a demo: <a href="https:&#x2F;&#x2F;www.youtube.com&#x2F;watch?v=ttMl96l9xPA" rel="nofollow">https:&#x2F;&#x2F;www.youtube.com&#x2F;watch?v=ttMl96l9xPA</a>.<p>Our biggest pain point with hosting agents was that you&#x27;d need to stitch together multiple pieces: packaging your agent, running it in a sandbox, streaming messages back to users, persisting state across turns, and managing getting files to and from the agent workspace.<p>We wanted something like Cog from Replicate, but for agents: a simple way to package agent code from a repo and serve it behind a clean API&#x2F;SDK. We wanted to provide a protocol to communicate with your agent, but not constraint the agent logic or harness itself.<p>On Terminal Use, you package your agent from a repo with a config.yaml and Dockerfile, then deploy it with our CLI. You define the logic of three endpoints (on_create, on_event, and on_cancel) which track the lifecycle of a task (conversation). The config.yaml contains details about resources, build context, etc.<p>Out of the box, we support Claude Agent SDK and Codex SDK agents. By support, we mean that we have an adapter that converts from the SDK message types to ours. If you&#x27;d like to use your own custom harness, you can convert and send messages with our types (Vercel AI SDK v6 compatible). For the frontend, we have a Vercel AI SDK provider that lets you use your agent with Vercel&#x27;s AI SDK, and have a messages module so that you don&#x27;t have to manage streaming and persistence yourself.<p>The part we think is most different is storage.<p>We treat filesystems as first-class primitives, separate from the lifecycle of a task. That means you can persist a workspace across turns, share it between different agents, or upload &#x2F; download files independent of the sandbox being active. Further, our filesystem SDK provides presigned urls which makes it easy for your users to directly upload and download files which means that you don&#x27;t need to proxy file transfer through your backend.<p>Since your agent logic and filesystem storage are decoupled, this makes it easy to iterate on your agents without worrying about the files in the sandbox: if you ship a bug, you can deploy and auto-migrate all your tasks to the new deployment. If you make a breaking change, you can specify that existing tasks stay on the existing version, and only new tasks use the new version.<p>We&#x27;re also adding support for multi-filesystem mounts with configurable mount paths and read&#x2F;write modes, so storage stays durable and reusable while mount layout stays task-specific.<p>On the deployment side, we&#x27;ve been influenced by modern developer platforms: simple CLI deployments, preview&#x2F;production environments, git-based environment targeting, logs, and rollback. All the configuration you need to build, deploy &amp; manage resources for your agent is stored in the config.yaml file which makes it easy to build &amp; deploy your agent in CI&#x2F;CD pipelines.<p>Finally, we&#x27;ve explicitly designed our platform for your CLI coding agents to help you build, test, &amp; iterate with your agents. With our CLI, your coding agents can send messages to your deployed agents, and download filesystem contents to help you understand your agent&#x27;s output. A common way we test our agents is that we make markdown files with user scenarios we&#x27;d like to test, and then ask Claude Code to impersonate our users and chat with our deployed agent.<p>What we do not have yet: full parity with general-purpose sandbox providers. For example, preview URLs and lower-level sandbox.exec(...) style APIs are still on the roadmap.<p>We&#x27;re excited to hear any thoughts, insights, questions, and concerns in the comments below!
分数：40
评论数：20

## 调试信息
- Prompt：`/Users/sam/Documents/AI Models/ai_radar/outputs/debug/prompts/20260310_032327_hackernews_47311657_prompt.txt`
- Response：`/Users/sam/Documents/AI Models/ai_radar/outputs/debug/responses/20260310_032327_hackernews_47311657_response.txt`