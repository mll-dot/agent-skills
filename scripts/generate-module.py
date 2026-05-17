#!/usr/bin/env python3
"""
Android 组件化模块脚手架生成器（通用版）

自动探测项目配置，生成业务模块或统一 router 模块的目录结构和 build.gradle。

用法:
  python generate-module.py --name at_login --package com.example.app.login
  python generate-module.py --name router --package com.example.router --type router
  python generate-module.py --name at_login --package com.example.app.login --project-root /path/to/project
"""

import argparse
import os
import re


def read_file(path):
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def detect_project_config(project_root):
    config = {
        'java_version': '17',
        'namespace': '',
        'has_compose': False,
        'has_databinding': True,
        'compose_compiler_version': '',
        'routing_lib': '',
        'routing_apt': '',
        'routing_type': '',
        'base_modules': [],
        'common_module': '',
        'is_app_switch': False,
    }

    settings_path = os.path.join(project_root, 'settings.gradle')
    settings_kts_path = os.path.join(project_root, 'settings.gradle.kts')
    settings_content = read_file(settings_path) or read_file(settings_kts_path)

    app_gradle_path = os.path.join(project_root, 'app', 'build.gradle')
    app_gradle_kts_path = os.path.join(project_root, 'app', 'build.gradle.kts')
    app_gradle_content = read_file(app_gradle_path) or read_file(app_gradle_kts_path)

    root_gradle_path = os.path.join(project_root, 'build.gradle')
    root_gradle_kts_path = os.path.join(project_root, 'build.gradle.kts')
    root_gradle_content = read_file(root_gradle_path) or read_file(root_gradle_kts_path)

    config_path = os.path.join(project_root, 'config.gradle')
    config_content = read_file(config_path)

    gradle_props_path = os.path.join(project_root, 'gradle.properties')
    gradle_props_content = read_file(gradle_props_path)

    all_gradle = settings_content + '\n' + app_gradle_content + '\n' + root_gradle_content + '\n' + config_content

    ns_match = re.search(r'namespace\s+[\'"]([^\'"]+)[\'"]', app_gradle_content)
    if ns_match:
        config['namespace'] = ns_match.group(1)

    app_id_match = re.search(r'applicationId\s+[\'"]([^\'"]+)[\'"]', app_gradle_content)
    if app_id_match and not config['namespace']:
        config['namespace'] = app_id_match.group(1)

    java_match = re.search(r'sourceCompatibility\s+JavaVersion\.VERSION_(\d+)', all_gradle)
    if java_match:
        config['java_version'] = java_match.group(1)

    compose_match = re.search(r'compose\s*=\s*true', app_gradle_content)
    config['has_compose'] = bool(compose_match)

    compose_compiler_match = re.search(r'kotlinCompilerExtensionVersion\s+[\'"]([^\'"]+)[\'"]', all_gradle)
    if compose_compiler_match:
        config['compose_compiler_version'] = compose_compiler_match.group(1)

    if 'therouter' in all_gradle.lower():
        version_match = re.search(r'cn\.therouter:(?:apt|router):([^\s\'"]+)', all_gradle)
        version = version_match.group(1) if version_match else '1.3.0'
        config['routing_lib'] = f'cn.therouter:router:{version}'
        config['routing_apt'] = f'cn.therouter:apt:{version}'
        config['routing_type'] = 'therouter'
    elif 'arouter' in all_gradle.lower():
        version_match = re.search(r'com\.alibaba:arouter-(?:api|compiler):([^\s\'"]+)', all_gradle)
        version = version_match.group(1) if version_match else '1.5.2'
        config['routing_lib'] = f'com.alibaba:arouter-api:{version}'
        config['routing_apt'] = f'com.alibaba:arouter-compiler:{version}'
        config['routing_type'] = 'arouter'

    includes = re.findall(r"include\s+[\'\"]([^\'\"]+)[\'\"]", settings_content)
    base_keywords = ['common', 'library', 'ui', 'network', 'base', 'core', 'utils', 'widget']
    business_keywords = ['app', 'login', 'order', 'user', 'home', 'hotel', 'cashier', 'cart', 'profile', 'mine', 'setting', 'search', 'message', 'pay', 'webview']

    for inc in includes:
        parts = inc.split(':')[-1].lower()
        is_base = any(kw in parts for kw in base_keywords) and not any(kw in parts for kw in business_keywords)
        if is_base:
            config['base_modules'].append(inc)

    if config['base_modules']:
        for bm in config['base_modules']:
            name = bm.split(':')[-1].lower()
            if 'common' in name:
                config['common_module'] = bm
                break
        if not config['common_module']:
            config['common_module'] = config['base_modules'][0]

    if 'isApplication' in gradle_props_content or 'isApplication' in all_gradle:
        config['is_app_switch'] = True

    return config


def module_name_to_dir(module_name):
    return module_name.replace(':', os.sep)


def module_name_to_resource_prefix(module_name):
    parts = module_name.split(':')
    name = parts[-1].replace('_', '')
    return name + '_'


def package_to_path(package_name):
    return package_name.replace('.', os.sep)


def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  Created: {path}')


BUSINESS_GRADLE_TEMPLATE = '''{apply_plugin_block}
apply plugin: 'kotlin-android'
apply plugin: 'kotlin-kapt'

android {{
    namespace '{namespace}'
    compileSdk rootProject.ext.android.compileSdkVersion

    defaultConfig {{
        {app_id_block}
        minSdk rootProject.ext.android.minSdkVersion
        targetSdk rootProject.ext.android.targetSdkVersion
        versionCode rootProject.ext.android.versionCode
        versionName rootProject.ext.android.versionName
    }}

    buildTypes {{
        release {{
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
    }}

    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_{java_version}
        targetCompatibility JavaVersion.VERSION_{java_version}
    }}

    kotlinOptions {{
        jvmTarget = '{java_version}'
    }}

    buildFeatures {{
        dataBinding = true{compose_block}
    }}
{compose_options_block}
    resourcePrefix '{resource_prefix}'
}}

dependencies {{
{base_deps_block}
    kapt "{routing_apt}"
}}
'''

ROUTER_GRADLE_TEMPLATE = '''apply plugin: 'com.android.library'
apply plugin: 'kotlin-android'

android {{
    namespace '{namespace}'
    compileSdk rootProject.ext.android.compileSdkVersion

    defaultConfig {{
        minSdk rootProject.ext.android.minSdkVersion
        targetSdk rootProject.ext.android.targetSdkVersion
    }}

    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_{java_version}
        targetCompatibility JavaVersion.VERSION_{java_version}
    }}

    kotlinOptions {{
        jvmTarget = '{java_version}'
    }}
}}

dependencies {{
{common_dep}
    implementation "{routing_lib}"
}}
'''

MANIFEST_TEMPLATE = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
</manifest>
'''

PROGUARD_TEMPLATE = '''# Add module-specific ProGuard rules here
'''

DEBUG_MANIFEST_TEMPLATE = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:name=".DebugApp"
        android:allowBackup="false"
        android:label="{module_name} Debug"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar">
    </application>
</manifest>
'''

DEBUG_APP_TEMPLATE = '''package {package_name}

import android.app.Application
{routing_import}

class DebugApp : Application() {{
    override fun onCreate() {{
        super.onCreate()
        {routing_init}
    }}
}}
'''


def generate_business_module(module_name, package_name, project_root, config):
    module_dir = os.path.join(project_root, module_name_to_dir(module_name))
    src_dir = os.path.join(module_dir, 'src', 'main', 'java', package_to_path(package_name))
    res_dir = os.path.join(module_dir, 'src', 'main', 'res')
    debug_src_dir = os.path.join(module_dir, 'src', 'debug', 'java', package_to_path(package_name))

    resource_prefix = module_name_to_resource_prefix(module_name)
    namespace = package_name
    java_version = config['java_version']

    if config['is_app_switch']:
        apply_plugin = '''if (rootProject.ext.isApplication) {
    apply plugin: 'com.android.application'
} else {
    apply plugin: 'com.android.library'
}'''
        app_id_block = f'''if (rootProject.ext.isApplication) {{
            applicationId "{namespace}"
        }}'''
    else:
        apply_plugin = "apply plugin: 'com.android.library'"
        app_id_block = ''

    compose_block = ''
    compose_options_block = ''
    if config['has_compose']:
        compose_block = '\n        compose = true'
        if config['compose_compiler_version']:
            compose_options_block = f"""
    composeOptions {{
        kotlinCompilerExtensionVersion '{config['compose_compiler_version']}'
    }}
"""

    base_deps_block = ''
    ui_module = None
    for bm in config['base_modules']:
        name = bm.split(':')[-1].lower()
        if 'ui' in name:
            ui_module = bm
            break

    if ui_module:
        base_deps_block = f'    api project(path: \':{ui_module}\')\n'
    else:
        for bm in config['base_modules']:
            base_deps_block += f'    api project(path: \':{bm}\')\n'

    gradle_content = BUSINESS_GRADLE_TEMPLATE.format(
        apply_plugin_block=apply_plugin,
        namespace=namespace,
        app_id_block=app_id_block,
        java_version=java_version,
        resource_prefix=resource_prefix,
        base_deps_block=base_deps_block,
        compose_block=compose_block,
        compose_options_block=compose_options_block,
        routing_apt=config.get('routing_apt', 'UNKNOWN'),
    )

    create_file(os.path.join(module_dir, 'build.gradle'), gradle_content)
    create_file(os.path.join(module_dir, 'proguard-rules.pro'), PROGUARD_TEMPLATE)
    create_file(os.path.join(module_dir, 'src', 'main', 'AndroidManifest.xml'), MANIFEST_TEMPLATE)

    for ui_subdir in ['activity', 'fragment', 'compose', 'dialog']:
        ui_dir = os.path.join(src_dir, 'ui', ui_subdir)
        os.makedirs(ui_dir, exist_ok=True)
        print(f'  Created: {ui_dir}')

    for subdir in ['viewmodel', 'adapter', 'api', 'service']:
        os.makedirs(os.path.join(src_dir, subdir), exist_ok=True)
        print(f'  Created: {os.path.join(src_dir, subdir)}')

    for model_subdir in ['request', 'response', 'bean']:
        model_dir = os.path.join(src_dir, 'model', model_subdir)
        os.makedirs(model_dir, exist_ok=True)
        print(f'  Created: {model_dir}')

    for util_subdir in ['manager', 'helper']:
        util_dir = os.path.join(src_dir, 'utils', util_subdir)
        os.makedirs(util_dir, exist_ok=True)
        print(f'  Created: {util_dir}')

    for res_subdir in ['layout', 'drawable', 'values']:
        os.makedirs(os.path.join(res_dir, res_subdir), exist_ok=True)
        print(f'  Created: {os.path.join(res_dir, res_subdir)}')

    if config['is_app_switch']:
        routing_type = config.get('routing_type', '')
        if routing_type == 'therouter':
            routing_import = 'import com.therouter.TheRouter'
            routing_init = 'TheRouter.init(this)'
        elif routing_type == 'arouter':
            routing_import = 'import com.alibaba.android.arouter.launcher.ARouter'
            routing_init = 'ARouter.init(this)'
        else:
            routing_import = '// import your routing framework'
            routing_init = '// init your routing framework'

        create_file(
            os.path.join(debug_src_dir, 'DebugApp.kt'),
            DEBUG_APP_TEMPLATE.format(
                package_name=package_name,
                routing_import=routing_import,
                routing_init=routing_init,
            ),
        )
        create_file(
            os.path.join(module_dir, 'src', 'debug', 'AndroidManifest.xml'),
            DEBUG_MANIFEST_TEMPLATE.format(module_name=module_name),
        )

    print(f'\n  Module created at: {module_dir}')
    print(f'  Remember to add to settings.gradle: include \':{module_name}\')
    print(f'  Note: router is included transitively via {ui_module or "base modules"}')

    if not config.get('routing_lib'):
        print(f'  WARNING: No routing framework detected. Please configure routing dependencies manually.')


def generate_router_module(module_name, package_name, project_root, config):
    module_dir = os.path.join(project_root, module_name_to_dir(module_name))
    src_dir = os.path.join(module_dir, 'src', 'main', 'java', package_to_path(package_name))

    namespace = package_name
    java_version = config['java_version']

    common_dep = ''
    if config.get('common_module'):
        common_dep = f'    implementation project(path: \':{config["common_module"]}\')\n'

    gradle_content = ROUTER_GRADLE_TEMPLATE.format(
        namespace=namespace,
        java_version=java_version,
        common_dep=common_dep,
        routing_lib=config.get('routing_lib', 'UNKNOWN'),
    )

    create_file(os.path.join(module_dir, 'build.gradle'), gradle_content)
    create_file(os.path.join(module_dir, 'src', 'main', 'AndroidManifest.xml'), MANIFEST_TEMPLATE)

    for subdir in ['constants', 'service', 'model']:
        os.makedirs(os.path.join(src_dir, subdir), exist_ok=True)
        print(f'  Created: {os.path.join(src_dir, subdir)}')

    print(f'\n  Router module created at: {module_dir}')
    print(f'  Remember to add to settings.gradle: include \':{module_name}\')

    if not config.get('routing_lib'):
        print(f'  WARNING: No routing framework detected. Please configure routing dependencies manually.')


def main():
    parser = argparse.ArgumentParser(description='Generate Android module scaffold (universal)')
    parser.add_argument('--name', required=True, help='Module name (e.g., at_login or router)')
    parser.add_argument('--package', required=True, help='Package name (e.g., com.example.app.login)')
    parser.add_argument('--type', choices=['business', 'router'], default='business',
                        help='Module type: business (default) or router')
    parser.add_argument('--project-root', default='.', help='Project root directory')

    args = parser.parse_args()

    project_root = os.path.abspath(args.project_root)

    print(f'\nDetecting project configuration from: {project_root}')
    config = detect_project_config(project_root)

    print(f'  Namespace: {config["namespace"] or "(not detected)"}')
    print(f'  Java version: {config["java_version"]}')
    print(f'  Compose: {config["has_compose"]}')
    print(f'  Routing: {config.get("routing_lib", "(not detected)"}')
    print(f'  Base modules: {config["base_modules"] or "(none detected)"}')
    print(f'  Common module: {config["common_module"] or "(not detected)"}')
    print(f'  isApplication switch: {config["is_app_switch"]}')
    print()

    print(f'Generating {args.type} module: {args.name}')
    print(f'Package: {args.package}\n')

    if args.type == 'router':
        generate_router_module(args.name, args.package, project_root, config)
    else:
        generate_business_module(args.name, args.package, project_root, config)

    print('\nDone!')


if __name__ == '__main__':
    main()
