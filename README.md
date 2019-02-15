<h1>cc数据管理系统</h1>
项目是2017年8月的已部署上线的商用作品.目前正在更新与重构<br>
<h2>项目结构</h2>

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

数据管理系统.xmind  部分功能逻辑思维导图

<h2>技术栈</h2>
<h3>web框架</h3>
    Flask
<h3>数据库</h3>
    sqlite<br>
    Flask-SQLAlchemy<br>
    Redis<br>
<h3>前端</h3>
    jquery<br>
    bootstrap<br>
    font-awesome       图标与字体<br>
    sortable-master    前端支持拖动排序的组件<br>
    echarts            一款数据可视化前端组件<br>
<h2>项目部署</h2>
AWS Services  亚马逊服务器<br>
Nginx + uwsgi + redis


