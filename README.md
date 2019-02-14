**cc data management**
此项目还在施工中
项目是一年半前的作品.目前正在更新与重构
**项目结构**
--error_log  错误处理相关
--mail       邮件功能相关
--model      ORM模型与CURD相关功能的集成
--modules    业务核心功能包
    --admin             管理员权限相关
    --backup            自动备份相关
    --business          项目的核心业务包,所有核心业务逻辑都在这.
    --permission        权限验证装饰器相关
    --manage            后台管理相关
    --reconciliation    对账与财务报表相关
--plugins    插件包
    --common            全局通用插件库
--static     静态资源相关
--templates  html页面相关
**技术栈**
web框架
    *Flask
数据库
    *sqlite
    *Flask-SQLAlchemy
    
