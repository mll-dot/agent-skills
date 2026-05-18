# 模块模板

以下模板中的 `{{变量}}` 需要根据项目探测结果填充。具体值来源：

| 变量 | 来源 |
|------|------|
| `{{NAMESPACE}}` | app 模块的 namespace 或 applicationId |
| `{{MODULE_NAME}}` | 用户指定的模块名 |
| `{{RESOURCE_PREFIX}}` | 根据模块名生成（如 `login_`） |
| `{{ROUTER_MODULE}}` | 统一的路由模块名（默认为 `basic:router`） |
| `{{JAVA_VERSION}}` | 项目 compileOptions 中的 Java 版本 |
| `{{ROUTING_APT_COORD}}` | 路由注解处理器 Maven 坐标 |
| `{{ROUTING_LIB_COORD}}` | 路由库 Maven 坐标 |
| `{{BASE_UI_MODULE}}` | 项目基础 UI 模块的 Gradle 路径 |
| `{{BASE_LIB_MODULE}}` | 项目基础能力模块的 Gradle 路径 |
| `{{BASE_COMMON_MODULE}}` | 项目最底层公共模块的 Gradle 路径 |
| `{{COMPOSE_COMPILER_VERSION}}` | 项目 composeOptions 中的版本 |

---

## 业务模块 build.gradle

```groovy
if (rootProject.ext.isApplication) {
    apply plugin: 'com.android.application'
} else {
    apply plugin: 'com.android.library'
}
apply plugin: 'kotlin-android'
apply plugin: 'kotlin-kapt'

android {
    namespace '{{NAMESPACE}}'
    compileSdk rootProject.ext.android.compileSdkVersion

    defaultConfig {
        if (rootProject.ext.isApplication) {
            applicationId "{{NAMESPACE}}"
        }
        minSdk rootProject.ext.android.minSdkVersion
        targetSdk rootProject.ext.android.targetSdkVersion
        versionCode rootProject.ext.android.versionCode
        versionName rootProject.ext.android.versionName
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_{{JAVA_VERSION}}
        targetCompatibility JavaVersion.VERSION_{{JAVA_VERSION}}
    }

    kotlinOptions {
        jvmTarget = '{{JAVA_VERSION}}'
    }

    buildFeatures {
        dataBinding = true
        compose = true  // 根据项目实际情况，不用 Compose 则删除
    }

    composeOptions {
        kotlinCompilerExtensionVersion '{{COMPOSE_COMPILER_VERSION}}'
    }

    resourcePrefix '{{RESOURCE_PREFIX}}'
}

dependencies {
    // 基础层（router 会通过 basic:library 传递依赖，无需直接依赖）
    api project(path: ':{{BASE_UI_MODULE}}')

    // 路由注解处理器（每个使用 @Route 的模块都需要）
    kapt "{{ROUTING_APT_COORD}}"

    // 其他依赖按需添加
}
```

## router 模块 build.gradle

```groovy
apply plugin: 'com.android.library'
apply plugin: 'kotlin-android'

android {
    namespace '{{NAMESPACE}}'
    compileSdk rootProject.ext.android.compileSdkVersion

    defaultConfig {
        minSdk rootProject.ext.android.minSdkVersion
        targetSdk rootProject.ext.android.targetSdkVersion
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_{{JAVA_VERSION}}
        targetCompatibility JavaVersion.VERSION_{{JAVA_VERSION}}
    }

    kotlinOptions {
        jvmTarget = '{{JAVA_VERSION}}'
    }
}

dependencies {
    // 路由框架（router 模块定义接口和常量，不需要 kapt）
    implementation "{{ROUTING_LIB_COORD}}"
}
```

## 模块目录结构

**根据业务量选择分包策略：页面 ≥ 3 个用按页面分包，页面 < 3 个用按类型扁平分包。**

### 方式一：按页面分包（页面 ≥ 3 个，业务较多时使用）

同一页面的 Activity、Fragment、ViewModel、Adapter 放在一起：

```
{{MODULE_NAME}}/
├── build.gradle
├── proguard-rules.pro
└── src/
    ├── main/
    │   ├── AndroidManifest.xml
    │   ├── java/
    │   │   └── {{包路径}}/
    │   │       ├── ui/
    │   │       │   ├── login/                    # 按页面聚合
    │   │       │   │   ├── LoginActivity.kt
    │   │       │   │   ├── LoginFragment.kt
    │   │       │   │   ├── LoginViewModel.kt
    │   │       │   │   └── LoginAdapter.kt
    │   │       │   ├── register/
    │   │       │   │   ├── RegisterActivity.kt
    │   │       │   │   └── RegisterViewModel.kt
    │   │       │   └── common/                   # 页面间复用的 UI 组件
    │   │       │       ├── dialog/
    │   │       │       ├── adapter/
    │   │       │       └── widget/
    │   │       ├── api/
    │   │       ├── service/
    │   │       ├── model/
    │   │       │   ├── request/
    │   │       │   ├── response/
    │   │       │   └── bean/
    │   │       └── utils/
    │   │           ├── manager/
    │   │           └── helper/
    │   └── res/
    │       ├── layout/
    │       ├── drawable/
    │       └── values/
    └── debug/                    # 独立调试用
        ├── java/
        │   └── {{包路径}}/
        │       └── DebugApp.kt
        └── AndroidManifest.xml  # 含 LAUNCHER Activity
```

### 方式二：按类型扁平分包（页面 < 3 个，业务较少时使用）

无需在 ui 下新建业务包，直接按类型分类：

```
{{MODULE_NAME}}/
├── build.gradle
├── proguard-rules.pro
└── src/
    ├── main/
    │   ├── AndroidManifest.xml
    │   ├── java/
    │   │   └── {{包路径}}/
    │   │       ├── ui/
    │   │       │   ├── activity/               # 所有 Activity
    │   │       │   │   └── XxxActivity.kt
    │   │       │   ├── adapter/                # 所有 Adapter
    │   │       │   │   └── XxxAdapter.kt
    │   │       │   ├── dialog/                 # 所有 Dialog、DialogFragment
    │   │       │   │   └── XxxDialog.kt
    │   │       │   ├── fragment/               # 所有 Fragment（如有）
    │   │       │   │   └── XxxFragment.kt
    │   │       │   └── viewmodel/              # 所有 ViewModel（数量少也可直接放 ui/ 下）
    │   │       │       └── XxxViewModel.kt
    │   │       ├── api/
    │   │       ├── service/
    │   │       ├── model/
    │   │       │   ├── request/
    │   │       │   ├── response/
    │   │       │   └── bean/
    │   │       └── utils/
    │   │           ├── manager/
    │   │           └── helper/
    │   └── res/
    │       ├── layout/
    │       ├── drawable/
    │       └── values/
    └── debug/                    # 独立调试用
        ├── java/
        │   └── {{包路径}}/
        │       └── DebugApp.kt
        └── AndroidManifest.xml  # 含 LAUNCHER Activity
```

---

**分包原则：**

- **页面 ≥ 3 个（业务较多）→ 按页面分包**：同一页面的 Activity、Fragment、ViewModel、Adapter 放在同一个目录下，改一个页面不用跳多个文件夹
- **页面 < 3 个（业务较少）→ 按类型扁平分包**：直接用 `activity/`、`adapter/`、`dialog/`、`fragment/`、`viewmodel/` 分类，避免过度拆分增加不必要的目录层级
- 页面目录命名用小驼峰，如 `login/`、`orderDetail/`、`settings/`

**子目录说明：**

| 目录 | 用途 |
|------|------|
| `ui/{page}/` | 按页面聚合（业务较多时），包含该页面的 Activity、Fragment、ViewModel、Adapter 等 |
| `ui/activity/` | 所有 Activity（业务较少时） |
| `ui/adapter/` | 所有 Adapter（业务较少时）或跨页面复用的 Adapter（业务较多时放在 `ui/common/adapter/`） |
| `ui/dialog/` | 所有 Dialog、DialogFragment（业务较少时）或跨页面复用的 Dialog（业务较多时放在 `ui/common/dialog/`） |
| `ui/fragment/` | 所有 Fragment（业务较少时） |
| `ui/viewmodel/` | 所有 ViewModel（业务较少时，数量少也可直接放 ui/ 下） |
| `ui/common/` | 跨页面复用的 UI 组件（仅按页面分包时使用） |
| `api/` | Retrofit/OkHttp 接口定义 |
| `service/` | 业务服务接口和内部实现 |
| `model/request/` | 请求参数模型 |
| `model/response/` | 响应数据模型 |
| `model/bean/` | 通用数据 Bean、DTO |
| `utils/manager/` | 单例管理器类 |
| `utils/helper/` | 辅助工具类 |

**注意：** 迁移已有模块时，不需要强行把现有文件搬去这个结构。上述结构是"应该怎么放"，现有代码"在哪就放哪"，先迁过去再说。

## router 目录结构

```
{{ROUTER_MODULE}}/
├── build.gradle
└── src/
    └── main/
        ├── java/
        │   └── {{包路径}}/
        │       ├── constants/
        │       │   └── RouterXxxConstants.kt
        │       ├── service/
        │       │   └── XxxService.kt
        │       └── model/
        │           └── XxxModel.kt
        └── AndroidManifest.xml
```

**router 模块只放接口和常量，不放任何业务实现代码。**

| 子目录 | 用途 |
|--------|------|
| `constants/` | 路由路径常量、其他跨模块共享的常量 |
| `service/` | 服务接口定义（只有 interface，没有实现） |
| `model/` | 跨模块共享的数据模型（DTO、Bean） |

## 独立调试 AndroidManifest.xml（debug 目录）

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:name=".DebugApp"
        android:allowBackup="false"
        android:label="{{MODULE_NAME}} Debug"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar">
        <activity
            android:name="{{包名}}.ui.xxx.XxxActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

## 独立调试 Application 类

```kotlin
package {{包名}}

import android.app.Application

class DebugApp : Application() {
    override fun onCreate() {
        super.onCreate()
        // 根据路由方案调用初始化
        // TheRouter: TheRouter.init(this)
        // ARouter: ARouter.init(this)
    }
}
```
