# Agent Skills

opencode agent 技能集合。

## android-modularize

Android 项目组件化迁移技能，用于将单体 app 模块中的业务代码逐步拆分到独立业务模块，实现组件化架构。

### 功能

- 自动探测项目配置（路由方案、模块命名风格、基础模块等）
- 逐步拆分业务模块，每次只拆一个，拆完验证再拆下一个
- 生成模块模板代码和目录结构
- 配置模块间路由通信
- 处理模块间依赖关系

### 安装

```bash
opencode skill add https://github.com/mazhenlei/agent-skills.git android-modularize
```

### 使用

安装后，在 opencode 中提到"组件化"、"模块拆分"、"拆模块"等关键词即可自动触发该技能。

### 触发关键词

组件化、模块拆分、模块化、拆模块、迁移业务代码、抽模块、解耦、独立编译

## License

MIT
