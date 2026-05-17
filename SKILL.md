---
name: android-modularize
description: |
  Android 项目组件化迁移技能。用于将单体 app 模块中的业务代码逐步拆分到独立业务模块，
  实现组件化架构。当用户提到"组件化"、"模块拆分"、"模块化"、"拆模块"、"迁移业务代码"、
  "抽模块"、"解耦"、"独立编译"等关键词时触发此技能。也适用于用户想要把某个业务包
  从 app 模块移到独立模块、创建 router 模块、配置模块间路由通信、或处理模块间
  依赖关系的场景。即使用户只是提到"这个功能能不能独立出去"或"我想把 XX 拆出来"，
  也应该使用此技能。
---

# Android 组件化迁移技能

你正在帮助用户将一个 Android 单体项目逐步拆分为组件化架构。

核心原则：**每次只拆一个模块，拆完验证通过再拆下一个。不求快，求稳。**

---

## 首次使用：探测项目配置

在开始拆分工作之前，必须先探测项目配置，后续所有步骤都依赖这些信息。读取以下内容并记录：

| 配置项 | 探测方式 |
|--------|---------|
| **app 包名** | 读取 `app/build.gradle` 的 `namespace` 或 `applicationId` |
| **基础模块名** | 读取 `settings.gradle`，找出非业务模块（common、library、ui、network 等基础设施模块） |
| **路由方案** | 搜索 `build.gradle` 中的依赖：`therouter` / `arouter` / 其他；搜索代码中的注解：`@Route`、`@Autowired`、`@Interceptor` |
| **路由版本** | 从 `build.gradle` 依赖声明中提取 |
| **Java/Kotlin 版本** | 读取 `compileOptions` 和 `kotlinOptions` |
| **是否使用 Compose** | 检查 `buildFeatures.compose` 和 `composeOptions` |
| **是否使用 DataBinding** | 检查 `buildFeatures.dataBinding` |
| **已有的业务模块** | 读取 `settings.gradle`，找出已有业务模块（含 `src/main/java/` 有代码的） |
| **空壳业务模块** | 识别 `settings.gradle` 中已 include 但 `src/main/java/` 无代码的模块 |
| **模块命名风格** | 观察已有模块命名（如 `at_xxx`、`lib_xxx`、`module_xxx`、`feature_xxx`），新模块保持一致 |
| **isApplication 开关** | 检查 `gradle.properties` 和已有模块 `build.gradle`，确认是否已配置独立调试开关 |

将探测结果整理后告诉用户确认，特别关注：
- 路由方案是否正确识别
- 基础模块列表是否完整

### 模块命名：主动建议，用户确认或自定义

根据探测到的命名风格，**主动给出建议的模块名、service-api 名和包名**，让用户选择用建议值还是自己改。不要直接问"你想叫什么"，而是给一个具体的推荐：

```
根据项目已有命名风格，建议：
- 业务模块名：at_login
- service-api 名：service:login-api
- 包名：com.atour.atourlife.login

你觉得可以吗？或者你想自定义名称？
```

建议规则：
- **业务模块名**：沿用项目已有前缀（`at_`、`lib_`、`module_`、`feature_`）+ 业务域名
- **service-api 名**：`service:` 前缀 + 业务域名 + `-api` 后缀，如果项目没有 service 层目录则直接用 `xxx-api`
- **包名**：沿用 app 包名前缀 + 业务域名，如项目习惯用独立包名则用独立包名

---

## 拆分工作流

当用户要求拆分某个业务模块时，按以下步骤执行：

### 第一步：确定拆分范围

1. 读取 `references/migration-checklist.md`，了解完整的拆分检查清单
2. 和用户确认要拆分的业务域（如登录、订单、用户中心等）
3. 在 app 模块中找到该业务域对应的包路径和所有相关文件
4. 识别该业务域与其他业务域之间的交叉依赖——这是拆分最难的部分

**识别文件归属的方法：**
- 以包路径为主要依据（如 `com.example.app.login` → 登录模块）
- 注意"名不副实"的情况：部分业务的 UI 可能散落在 `fragment/` 或 `activity/` 顶层目录中
- API 接口定义（Retrofit Service）通常在 `api/` 包下，需要按业务归属拆分
- ViewModel、Manager、Helper 等如果只服务单一业务域，跟随业务迁移

**遇到模糊归属时，问用户而不是猜。** 比如某个 ViewModel 同时被两个业务使用，应该问用户它归哪个模块。

### 第二步：创建或确认模块脚手架

**先检查目标模块是否已存在。** 扫描项目目录和 `settings.gradle`，如果模块目录和 build.gradle 已经在，直接跳过创建，只需确认以下内容齐全即可继续：

- [ ] 模块目录存在
- [ ] `build.gradle` 已配置（含路由注解处理器、基础依赖、isApplication 开关）
- [ ] `src/main/AndroidManifest.xml` 存在
- [ ] `settings.gradle` 中已 include 该模块
- [ ] `app/build.gradle` 中已依赖该模块

如果模块尚不存在，运行 `scripts/generate-module.py` 生成：

```bash
python scripts/generate-module.py --name <模块名> --package <包名> --project-root <项目根目录>
```

这会创建：
- 模块目录
- `build.gradle`（含路由注解处理器、基础依赖、isApplication 开关）
- `src/main/AndroidManifest.xml`
- `src/main/java/` 包目录结构
- `proguard-rules.pro`

如果没有 Python 环境，手动创建。模板见 `references/module-template.md`，根据探测到的项目配置填充模板变量。

然后在 `settings.gradle` 中添加 include，在 `app/build.gradle` 中添加依赖。

### 第三步：创建/确认统一的 router 模块

**所有路由相关的代码（常量、服务接口、共享数据模型）都放在一个统一的 router 模块里，不按业务拆分多个 service-api。**

**判断是否需要 router 模块：** 只要项目存在模块间通信（路由跳转、服务发现）就需要。

**先检查 router 模块是否已存在。** 扫描项目目录和 `settings.gradle`：
- 存在 → 跳过创建，继续往里面迁内容
- 不存在 → 创建

如果 router 模块尚不存在，运行脚本或手动创建：

**模块命名建议：** `router`（优先，简洁）或 `service:router`（有分层习惯），主动建议让用户确认。

```bash
python scripts/generate-module.py --name router --package com.example.router --type api --project-root <项目根目录>
```

router 模块只包含：
- `constants/` — 所有路由路径常量（不分业务，按业务放在不同文件）
- `service/` — 所有服务接口定义
- `model/` — 需要跨模块共享的数据模型（DTO/Bean）
- `helper/` — 路由辅助类

**不要在 router 模块里放任何业务实现代码。** 实现类放在对应的业务模块，仅把接口放 router。

router 模块的依赖关系：
```
router  -->  项目最底层公共模块（如 basic:common）+ 路由库
```

**所有业务模块统一依赖 router，不再按业务拆分 service-api。**

### 第四步：迁移代码

这是最核心也最容易出问题的步骤。按以下顺序迁移：

#### 4.1 先迁接口和常量 → router 模块

将路由常量、服务接口、共享数据模型迁入 router 模块（如果已经在 router 模块则跳过）。更新所有引用这些常量的地方。

**迁入规则：**
- `RouterXxxConstants` → `router/src/.../constants/`
- `XxxService` 接口 → `router/src/.../service/`
- 跨模块共享的 DTO/Bean → `router/src/.../model/`
- 路由辅助类 → `router/src/.../helper/`

**注意：** 不要迁实现类，只迁接口。`XxxServiceImpl` 放在对应的业务模块，仅接口放 router。

#### 4.2 再迁业务代码 → 业务模块

将 Activity、Fragment、ViewModel、Adapter、Dialog 等迁入业务模块。

**迁移时需要同步处理：**
- **资源文件**：layout、drawable、values 等从 app/res 迁入模块 res，确保 `resourcePrefix` 命名
- **R 类引用**：迁入新模块后 R 类变为模块自己的 R 类，DataBinding 的 R 引用需要注意
- **Manifest**：将 Activity 声明从 app/AndroidManifest.xml 移到模块 Manifest
- **路由注册**：确保目标 Activity 上的路由注解路径正确，且路由注解处理器已配置

#### 4.3 处理依赖：被迁代码引用了 app 中未迁移的类

迁移代码到新模块后，编译会发现新模块引用了还在 app 中的类。按以下决策链处理：

**第一步：判断被引用类的归属**

| 情况 | 判断 | 处理方式 |
|------|------|---------|
| 被引用类**仅服务当前业务域**（如 LoginHelper 只被登录模块用） | 应该一起迁过来 | 随当前模块一起迁移 |
| 被引用类**属于另一个业务域**（如订单模块引用了 UserBean） | 不该迁过来 | 通过 router 模块中定义的服务接口访问，或把共享数据模型放入 router |
| 被引用类**被多个业务域共用**（如 BaseResponse、通用的 Bean/Utils） | 属于公共层 | 下沉到项目公共模块或 `router` 模块 |
| 被引用类**目前只被当前业务用，但未来可能被其他业务用**（如支付能力） | 属于公共服务 | 放入 router 模块，定义服务接口 |

**第二步：执行迁移**

- **一起迁过来的**：直接移到当前模块，更新包路径即可
- **放入 router 的**：将共享数据模型（Bean/DTO）、Event 类、常量迁入 router，让新模块和 app 都依赖 router
- **下沉到公共模块的**：将通用工具类、基础数据模型迁入项目最底层公共模块，注意不能带入任何业务逻辑
- **通过接口解耦的**：在 router 定义服务接口，app 或原模块提供实现，新模块通过路由服务发现调用

**第三步：更新所有引用**

迁移共享类后，必须同步更新 app 模块和其他模块中对这些类的 import 路径。用全局搜索确认没有遗漏。

**不要试图一次性解决所有依赖。** 如果某个依赖暂时无法解耦，可以先在 app 模块中保留一个桥接类，后续迭代再处理。

#### 4.4 处理依赖：app 中未迁移代码引用了被迁走的类

反过来，app 中还没迁的代码也可能引用了已经迁到新模块或 router 的类。处理方式：

| 情况 | 处理方式 |
|------|---------|
| app 引用了迁入新模块的 Activity | 改用路由跳转 |
| app 引用了迁入新模块的 Manager/Helper | 通过 router 模块中的服务接口调用 |
| app 引用了迁入 router 的 Bean/常量 | app 依赖 router 模块即可，无需改代码 |
| app 引用了迁入公共模块的工具类 | app 本身已依赖公共模块，无需改代码 |

### 第五步：配置模块依赖

在业务模块的 `build.gradle` 中声明依赖。依赖声明需要根据探测到的项目配置填写，示例：

```groovy
dependencies {
    implementation project(path: ':router')      // 统一的 router 模块
    implementation project(path: ':基础UI模块')   // UI 基础组件
    implementation project(path: ':基础能力模块') // 网络等基础能力

    // 路由框架（根据探测结果填写具体坐标和版本）
    kapt "<路由注解处理器坐标>"
    implementation "<路由库坐标>"
}
```

**依赖规则（必须遵守）：**
```
app（壳） --> 所有业务模块
业务模块  --> basic:ui
basic:ui  --> basic:library (api)
basic:library --> basic:router (api) + basic:common (api)
basic:router --> 路由库
```

**关键设计：router 作为基础层的一部分**
- `basic:library` 使用 `api` 依赖 `basic:router`
- 业务模块通过 `basic:ui` → `basic:library` 传递链间接获得 `router`
- 业务模块**不需要**直接依赖 `:router`

**所有业务模块依赖同一个 router，不再按业务拆分多个 service-api。**

### 第六步：编译验证

1. 先确保模块单独编译通过：`./gradlew :<模块名>:assembleDebug`
2. 再确保全项目编译通过：`./gradlew assembleDebug`
3. 检查路由表是否正确生成（根据路由方案检查对应输出目录）
4. 运行 app，手动测试被迁移模块的功能入口和页面跳转

### 第七步：清理 app 模块

迁移完成后，清理 app 模块中的残留：
- 删除已迁移的源文件（确认没有遗漏引用后再删）
- 删除已迁移的资源文件
- 删除 AndroidManifest.xml 中已迁移的 Activity 声明
- 删除 app/build.gradle 中对已迁移代码的专用依赖（如果该依赖仅被迁移代码使用）

---

## 路由方案适配

不同路由方案的 API 差异较大，迁移时需要根据项目实际使用的方案来写代码。

| 功能 | TheRouter | ARouter | 自研路由 |
|------|-----------|---------|---------|
| 页面跳转 | `TheRouter.build(path).navigation()` | `ARouter.getInstance().build(path).navigation()` | 按项目实际 API |
| 传参 | `.withString(key, value)` | `.withString(key, value)` | 按项目实际 API |
| 参数注入 | `@Autowired` + `TheRouter.inject(this)` | `@Autowired` + `ARouter.getInstance().inject(this)` | 按项目实际 API |
| 路由声明 | `@Route(path = "...")` | `@Route(path = "...")` | 按项目实际 API |
| 服务发现 | `TheRouter.get(XxxService::class.java)` | `ARouter.getInstance().navigation(XxxService::class.java)` | 按项目实际 API |
| 拦截器 | `@Interceptor` + `RouterInterceptor` | `@Interceptor` + `IInterceptor` | 按项目实际 API |
| 注解处理器 | `kapt "cn.therouter:apt:<ver>"` | `kapt "com.alibaba:arouter-compiler:<ver>"` | 按项目实际配置 |

详细的路由使用模式见 `references/routing-patterns.md`。

---

## 常见问题处理

### 跨模块共享数据模型

两个模块都需要用同一个 Bean/Response 类时，将该类放入 router 模块。注意 router 中的数据模型应该是纯数据类（DTO），不包含业务逻辑。

### 网络请求接口（Retrofit Service）

各业务模块定义自己的 Retrofit API 接口，放在模块内的 `api/` 包下。API 实现由项目基础网络层统一提供 Retrofit 实例。

### 资源冲突

每个模块在 `build.gradle` 中配置 `resourcePrefix`，避免资源名冲突：
```groovy
android {
    resourcePrefix '<模块前缀>_'
}
```

### DataBinding 跨模块

DataBinding 的 BR 类和 layout 引用需要使用模块自己的 R 资源。如果 layout 中引用了其他模块的资源，需要通过 `?attr/` 主题属性或公共 UI 模块提供的公共样式解决。

### Application 初始化

业务模块的初始化逻辑根据路由方案选择：
- **TheRouter**：使用 `@ServiceProvider`
- **ARouter**：使用 `@Route(path = "/xxx/init")` + 服务发现
- **其他**：在 app 壳工程的 Application 中统一调用各模块的初始化入口

---

## 模块独立调试

每个业务模块支持独立运行，通过 `isApplication` 开关控制：

```groovy
if (rootProject.ext.isApplication) {
    apply plugin: 'com.android.application'
} else {
    apply plugin: 'com.android.library'
}
```

独立调试时需要：
1. 提供模块自己的 `Application` 类
2. 提供模块自己的 `AndroidManifest.xml`（含 LAUNCHER Activity）
3. 在 `gradle.properties` 中设置 `isApplication=true`（仅调试时）

---

## 参考文档

遇到具体问题时，查阅以下参考文档：

- `references/migration-checklist.md` — 每次迁移的完整检查清单
- `references/module-template.md` — 新模块的 build.gradle 和目录结构模板
- `references/routing-patterns.md` — 路由框架使用模式和服务接口设计规范
