import { defineConfig } from 'vitepress';

export default defineConfig({
  title: 'use-nacos',
  description: 'Python Nacos 客户端库',
  lang: 'zh-CN',
  themeConfig: {
    logo: '/logo.png',
    nav: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guide/' },
      { text: 'API', link: '/api/' },
      { text: 'GitHub', link: 'https://github.com/use-py/use-nacos' },
    ],
    sidebar: {
      '/guide/': [
        {
          text: '入门',
          items: [
            { text: '简介', link: '/guide/' },
            { text: '快速开始', link: '/guide/getting-started' },
          ],
        },

      ],
      '/api/': [
        {
          text: '客户端',
          items: [
            { text: '概述', link: '/api/' },
            { text: 'NacosClient', link: '/api/client' },
            { text: '认证', link: '/api/auth' },
          ],
        },
        {
          text: '服务管理',
          items: [
            { text: '服务 API', link: '/api/service' },
            { text: '实例 API', link: '/api/instance' },
            { text: '服务发现 API', link: '/api/discovery' },
          ],
        },
        {
          text: '配置管理',
          items: [
            { text: '配置 API', link: '/api/config' },
            { text: '序列化 API', link: '/api/serializer' },
            { text: '缓存 API', link: '/api/cache' },
          ],
        },
        {
          text: '错误处理',
          items: [
            { text: '异常 API', link: '/api/exception' },
          ],
        },
      ],
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/use-py/use-nacos' },
    ],
    footer: {
      message: '基于 Apache 2.0 许可发布',
      copyright: 'Copyright © 2024 use-nacos 团队',
    },
  },
});
