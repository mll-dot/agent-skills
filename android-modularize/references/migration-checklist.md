# 模块迁移检查清单

每次迁移一个业务模块前、中、后，逐项检查。

---

## 迁移前：确认范围

- [ ] 确认要迁移的业务域名称和目标模块名
- [ ] 列出 app 模块中属于该业务的所有源文件（按包路径扫描）
- [ ] 列出该业务使用的所有 layout 资源文件
- [ ] 列出该业务使用的 drawable/values 等其他资源
- [ ] 识别该业务的 AndroidManifest.xml 中的 Activity/Service/Receiver 声明
- [ ] 确认该业务是否有独立的 Retrofit API 接口（在 `api/` 包下）
- [ ] 识别该业务对其他业务模块的直接引用（跨业务 import）
- [ ] 识别其他业务模块对该业务的直接引用（反向依赖）
- [ ] 确认是否需要创建 service-api 模块
- [ ] 确认 EventBus/LiveData 等事件类是否需要跨模块共享
- [ ] 确认项目使用的路由方案及版本

## 迁移中：代码迁移

### service-api 模块（如需要）

- [ ] 创建 service-api 模块目录和 build.gradle
- [ ] 将路由常量类迁入 service-api
- [ ] 定义服务接口
- [ ] 将需要共享的数据模型迁入 service-api
- [ ] 将需要跨模块传递的 Event 类迁入 service-api
- [ ] service-api 的 build.gradle 只依赖项目最底层公共模块
- [ ] 在 settings.gradle 中 include service-api 模块

### 业务模块

- [ ] 创建或确认业务模块目录和 build.gradle
- [ ] 配置 resourcePrefix
- [ ] 配置 isApplication 开关（独立调试）
- [ ] 配置路由注解处理器（kapt/annotationProcessor）
- [ ] 根据该模块内页面数量选择分包策略：页面 ≥ 3 个建议按页面分包（同一页面的 Activity、Fragment、ViewModel、Adapter 放同一个包下），页面 < 3 个建议按类型扁平分包（ui/activity/、ui/adapter/、ui/dialog/ 等），如用户同意则按对应结构迁移
- [ ] 迁移源代码文件
- [ ] 迁移资源文件（layout、drawable、values 等）
- [ ] 迁移 AndroidManifest.xml 中的声明
- [ ] 迁移 proguard 规则（如有）
- [ ] 在 settings.gradle 中 include 业务模块

### 依赖处理

- [ ] 将直接类引用跳转替换为路由跳转
- [ ] 将跨业务直接调用替换为路由服务发现
- [ ] 判断被引用类归属：仅服务当前业务 → 一起迁；属于其他业务 → 接口解耦；多业务共用 → 下沉公共层
- [ ] 更新 app 模块中对该业务的 import（改为通过 service-api）
- [ ] 更新其他业务模块中对该业务的引用
- [ ] 处理事件总线：共享 Event 放入 service-api，模块内部 Event 留在模块内
- [ ] 检查是否有循环依赖

### 构建配置

- [ ] 在 app/build.gradle 添加对业务模块的依赖
- [ ] 业务模块的 build.gradle 声明对 service-api 和基础层的依赖
- [ ] 添加路由注解处理器配置
- [ ] 检查是否有仅在 app 模块使用的依赖被误迁到业务模块

## 迁移后：验证

- [ ] `./gradlew :<模块名>:assembleDebug` 单模块编译通过
- [ ] `./gradlew assembleDebug` 全项目编译通过
- [ ] 检查路由表生成（根据路由方案检查对应输出目录）
- [ ] 检查无路由编译期警告（如重复路由路径）
- [ ] 手动测试：从 app 其他页面跳转到迁移模块的页面
- [ ] 手动测试：迁移模块的页面跳转到其他模块页面
- [ ] 手动测试：迁移模块的返回键/返回栈行为正常
- [ ] 手动测试：迁移模块的数据加载和展示正常
- [ ] 检查迁移模块的资源在 Release 包中未被混淆/压缩
- [ ] 清理 app 模块中已迁移的文件和资源
- [ ] 清理 app/AndroidManifest.xml 中已迁移的声明
- [ ] 确认 git diff 中没有遗漏的硬编码引用
