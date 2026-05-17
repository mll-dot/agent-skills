# 路由框架使用模式

本文档涵盖 Android 主流路由方案在组件化中的使用模式。根据项目探测结果，使用对应的方案。

---

## 方案一：TheRouter

### 页面跳转

```kotlin
// 声明路由
@Route(path = "/login/activity/LoginActivity")
class UserLoginActivity : BaseActivity()

// 跳转
TheRouter.build("/login/activity/LoginActivity")
    .withString("key", value)
    .navigation(context)

// 参数自动注入
@Route(path = "/login/activity/LoginActivity")
class UserLoginActivity : BaseActivity() {
    @Autowired
    lateinit var key: String

    override fun onCreate(savedInstanceState: Bundle?) {
        TheRouter.inject(this)
        super.onCreate(savedInstanceState)
    }
}
```

### 服务发现

**推荐方式：@ServiceProvider 函数（本项目使用此方式）**

```kotlin
// 定义接口（在 basic:router 模块）
package com.atour.router.service

interface AtUserService {
    fun isLogin(): Boolean
    fun getUserInfo(): UserInfo?
    fun gotoUserCenter(context: Context)
}

// 实现服务（在业务模块，用 @ServiceProvider 注解函数）
package com.atour.user

import com.atour.router.service.AtUserService
import com.therouter.inject.ServiceProvider

@ServiceProvider
fun getAtUserService(): AtUserService {
    return object : AtUserService {
        override fun isLogin(): Boolean = LoginHelper.isLogin()
        override fun getUserInfo(): UserInfo? = UserRepository.getUser()
        override fun gotoUserCenter(context: Context) {
            TheRouter.build(RouterUserConstants.USER_CENTER)
                .navigation(context)
        }
    }
}

// 调用服务（在其他模块）
val userService = TheRouter.get(AtUserService::class.java)
if (userService?.isLogin() == true) { /* ... */ }
```

**备选方式：@Route 路径方式**

```kotlin
// 定义接口
interface LoginService {
    companion object {
        const val SERVICE_PATH = "/login/service"
    }
    fun isLogin(): Boolean
}

// 实现服务（用 @Route 注解类）
@Route(path = LoginService.SERVICE_PATH)
class LoginServiceImpl : LoginService {
    override fun isLogin(): Boolean = LoginHelper.isLogin()
}

// 调用服务
val loginService = TheRouter.get(LoginService::class.java)
```

**两种方式对比：**

| 方式 | 注解位置 | 适用场景 |
|------|---------|---------|
| `@ServiceProvider` 函数 | 函数上 | **本项目用此方式**，更灵活，支持匿名实现 |
| `@Route` 类 | 类上 | 需要命名实现类，路径全局唯一 |

### 拦截器（登录检查）

```kotlin
@Interceptor(name = "LoginInterceptor")
class LoginInterceptor : RouterInterceptor {
    override fun process(chain: RouterInterceptor.Chain): Any? {
        if (isLogin()) {
            return chain.proceed(chain.request())
        } else {
            TheRouter.build("/login/activity/LoginActivity").navigation(chain.request().context)
            return null
        }
    }
}
```

### 模块初始化

**注意：这是 `@ServiceProvider` 的另一种用法（与服务发现不同），用于自动初始化。**

```kotlin
// 使用 AndroidX Startup 的 Initializer 接口
@ServiceProvider
class LoginModuleInit : Initializer<Any> {
    override fun init(context: Context): Any? {
        // 模块初始化逻辑（应用启动时自动调用）
        return null
    }
    
    override fun dependencies(): MutableList<Class<out Initializer<*>>> {
        return mutableListOf()
    }
}
```

**与服务发现的区别：**
- **服务发现**：`@ServiceProvider` 注解在**返回接口的函数**上 → 运行时通过 `TheRouter.get()` 获取
- **模块初始化**：`@ServiceProvider` 注解在**实现 `Initializer` 的类**上 → 启动时自动执行

---

## 方案二：ARouter

### 页面跳转

```kotlin
// 声明路由
@Route(path = "/login/activity/LoginActivity")
class UserLoginActivity : BaseActivity()

// 跳转
ARouter.getInstance().build("/login/activity/LoginActivity")
    .withString("key", value)
    .navigation(context)

// 参数自动注入
@Route(path = "/login/activity/LoginActivity")
class UserLoginActivity : BaseActivity() {
    @Autowired
    lateinit var key: String

    override fun onCreate(savedInstanceState: Bundle?) {
        ARouter.getInstance().inject(this)
        super.onCreate(savedInstanceState)
    }
}
```

### 服务发现

```kotlin
// 定义接口（在 service-api 模块）
interface LoginService : IProvider {
    fun isLogin(): Boolean
    fun getUserInfo(): UserInfo?
    fun gotoLogin(context: Context, callback: LoginCallback?)
}

// 实现服务（在业务模块）
@Route(path = "/login/service")
class LoginServiceImpl : LoginService {
    override fun init(bundle: Bundle?) {}
    override fun isLogin(): Boolean = LoginHelper.isLogin()
    override fun getUserInfo(): UserInfo? = UserRepository.getUser()
    override fun gotoLogin(context: Context, callback: LoginCallback?) {
        ARouter.getInstance().build("/login/activity/LoginActivity")
            .withObject("callback", callback)
            .navigation(context)
    }
}

// 调用服务（在其他模块）
val loginService = ARouter.getInstance().navigation(LoginService::class.java)
if (loginService?.isLogin() == true) { /* ... */ }
```

### 拦截器

```kotlin
@Interceptor(priority = 1, name = "LoginInterceptor")
class LoginInterceptor : IInterceptor {
    override fun process(postcard: Postcard, callback: InterceptorCallback) {
        if (isLogin()) {
            callback.onContinue(postcard)
        } else {
            ARouter.getInstance().build("/login/activity/LoginActivity").navigation()
            callback.onInterrupt(null)
        }
    }
    override fun init(context: Context) {}
}
```

---

## 方案三：自研路由

如果项目使用自研路由方案，按项目实际 API 编写。核心原则不变：
- 页面跳转走路由，不直接引用 Activity 类
- 跨模块调用走服务接口，不直接 import 实现类
- 路由路径常量化，集中管理

---

## 通用：迁移时从直接引用到路由的典型场景

### 场景 A：页面跳转

```kotlin
// 迁移前
val intent = Intent(this, HotelDetailActivity::class.java)
intent.putExtra("hotelId", hotelId)
startActivity(intent)

// 迁移后（TheRouter）
TheRouter.build(RouterHotelConstants.HOTEL_DETAIL)
    .withString("hotelId", hotelId)
    .navigation(this)

// 迁移后（ARouter）
ARouter.getInstance().build(RouterHotelConstants.HOTEL_DETAIL)
    .withString("hotelId", hotelId)
    .navigation(this)
```

### 场景 B：获取数据

```kotlin
// 迁移前
val userInfo = LoginHelper.getUserInfo()

// 迁移后（TheRouter）
val loginService = TheRouter.get(LoginService::class.java)
val userInfo = loginService?.getUserInfo()

// 迁移后（ARouter）
val loginService = ARouter.getInstance().navigation(LoginService::class.java)
val userInfo = loginService?.getUserInfo()
```

### 场景 C：调用功能

```kotlin
// 迁移前
PayPlugin.startPay(this, orderInfo)

// 迁移后（通过服务接口）
val payService = TheRouter.get(PayService::class.java) // 或 ARouter
payService?.startPay(this, orderInfo)
```

### 场景 D：事件总线替换

```kotlin
// 迁移前
EventBus.getDefault().post(LogoutEvent())

// 迁移后（方案一：接口回调，推荐）
val userService = TheRouter.get(UserService::class.java)
userService?.notifyLogout()

// 迁移后（方案二：TheRouter 动作拦截器，适合一对多通知）
TheRouter.asyncAction("LogoutAction")

// 迁移后（方案三：ARouter 无直接对应，使用接口回调）
val userService = ARouter.getInstance().navigation(UserService::class.java)
userService?.notifyLogout()
```

**事件总线迁移策略：** 模块内部的事件总线可以保留；跨模块的事件应逐步替换为 service-api 接口回调。如果 Event 类需要被多个模块使用，将其放入 service-api 模块。

---

## 路由路径命名规范

```
/<业务域>/<类型>/<名称>

示例：
/login/activity/LoginActivity
/order/detail/OrderDetailActivity
/hotel/list/HotelListActivity
/user/fragment/UserCenterFragment
```

路径中的名称使用类名本身，保持可读性和唯一性。路径在全局必须唯一。

---

## 注意事项

- 参数注入必须在 `onCreate` 中调用对应的 `inject` 方法后才生效
- 服务发现是运行时解析，目标模块未集成时返回 null，调用方必须做 null 安全处理
- 路由路径全局唯一，重复路径会导致编译期警告和运行时覆盖
- 路由注解处理器的 kapt/annotationProcessor 配置必须在每个使用路由的模块的 build.gradle 中添加，不能只在 app 模块配置
- ARouter 需要在 Application 中调用 `ARouter.init(this)`，TheRouter 同理
