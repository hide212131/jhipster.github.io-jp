import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'doc',
      label: 'はじめに',
      id: 'getting-started',
    },
    {
      type: 'category',
      label: 'インストールとセットアップ',
      items: [
        {
          type: 'doc',
          label: 'JHipsterのインストール',
          id: 'environment/installation',
        },
        {
          type: 'doc',
          label: 'プロキシの設定',
          id: 'environment/configuring-a-corporate-proxy',
        },
        {
          type: 'category',
          label: 'IDEの設定',
          link: { type: 'doc', id: 'environment/configuring-ide/index' },
          items: [
            {
              type: 'doc',
              label: 'EclipseとMaven',
              id: 'environment/configuring-ide/configuring-ide-eclipse',
            },
            {
              type: 'doc',
              label: 'EclipseとGradle',
              id: 'environment/configuring-ide/configuring-ide-eclipse-gradle',
            },
            {
              type: 'doc',
              label: 'Intellij IDEA',
              id: 'environment/configuring-ide/configuring-ide-idea',
            },
            {
              type: 'doc',
              label: 'Visual Studio Code',
              id: 'environment/configuring-ide/configuring-ide-visual-studio-code',
            },
            {
              type: 'doc',
              label: 'Netbeans',
              id: 'environment/configuring-ide/configuring-ide-netbeans',
            },
          ],
        },
        {
          type: 'doc',
          label: 'Docker Compose',
          id: 'environment/docker-compose',
        },
        {
          type: 'category',
          label: 'Shellプラグイン',
          link: { type: 'doc', id: 'environment/shell-plugins/index' },
          items: [
            {
              type: 'doc',
              label: 'Oh-My-Zsh JHipsterプラグイン',
              id: 'environment/shell-plugins/oh-my-zsh',
            },
            {
              type: 'doc',
              label: 'Fisher JHipsterプラグイン',
              id: 'environment/shell-plugins/fisher',
            },
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'アプリケーションとエンティティの作成',
      items: [
        {
          type: 'doc',
          label: 'アプリケーションの作成',
          id: 'core-tasks/creating-an-app',
        },
        {
          type: 'doc',
          label: 'エンティティの作成',
          id: 'core-tasks/creating-an-entity',
        },
        { type: 'doc', label: 'DTOの作成', id: 'core-tasks/using-dtos' },
        {
          type: 'doc',
          label: 'リレーションシップの管理',
          id: 'core-tasks/managing-relationships',
        },
        {
          type: 'doc',
          label: '国際化',
          id: 'core-tasks/installing-new-languages',
        },
        {
          type: 'doc',
          label: 'アプリケーションのアップグレード',
          id: 'core-tasks/upgrading-an-application',
        },
      ],
    },
    {
      type: 'category',
      label: 'オプションの技術',
      items: [
        { type: 'doc', label: 'アプリケーションのセキュリティ', id: 'options/security' },
        {
          type: 'doc',
          label: 'エンティティのフィルタリング',
          id: 'options/entities-filtering',
        },
        {
          type: 'doc',
          label: 'Elasticsearchの使用',
          id: 'options/using-elasticsearch',
        },
        {
          type: 'doc',
          label: 'Websocketsの使用',
          id: 'options/using-websockets',
        },
        {
          type: 'doc',
          label: 'APIファーストな開発',
          id: 'options/doing-api-first-development',
        },
        { type: 'doc', label: 'キャッシュの使用', id: 'options/using-cache' },
        { type: 'doc', label: 'Oracleの使用', id: 'options/using-oracle' },
        { type: 'doc', label: 'MongoDBの使用', id: 'options/using-mongodb' },
        {
          type: 'doc',
          label: 'Couchbaseの使用',
          id: 'options/using-couchbase',
        },
        { type: 'doc', label: 'Neo4jの使用', id: 'options/using-neo4j' },
        {
          type: 'doc',
          label: 'Cassandraの使用',
          id: 'options/using-cassandra',
        },
        { type: 'doc', label: 'Kafkaの使用', id: 'options/using-kafka' },
        { type: 'doc', label: 'Pulsarの使用', id: 'options/using-pulsar' },
      ],
    },
    {
      type: 'category',
      label: 'JDL',
      items: [
        { type: 'doc', label: '概要', id: 'jdl/intro' },
        { type: 'doc', label: '入門', id: 'jdl/getting-started' },
        { type: 'doc', label: 'アプリケーション', id: 'jdl/applications' },
        { type: 'doc', label: 'エンティティとフィールド', id: 'jdl/entities-fields' },
        { type: 'doc', label: '列挙型', id: 'jdl/enums' },
        { type: 'doc', label: 'リレーションシップ', id: 'jdl/relationships' },
        { type: 'doc', label: 'オプション', id: 'jdl/options' },
        { type: 'doc', label: 'デプロイメント', id: 'jdl/deployments' },
        { type: 'doc', label: 'トラブルシューティング', id: 'jdl/troubleshooting' },
      ],
    },
    {
      type: 'category',
      label: '開発',
      items: [
        {
          type: 'doc',
          label: '開発環境で使用',
          id: 'development/development',
        },
        { type: 'doc', label: 'プロファイルの管理', id: 'development/profiles' },
        {
          type: 'doc',
          label: '共通アプリケーションプロパティ',
          id: 'development/common-application-properties',
        },
        { type: 'doc', label: '共通ポート', id: 'development/common-ports' },
        {
          type: 'doc',
          label: 'フロントエンドとAPIの分離',
          id: 'development/separating-front-end-and-api',
        },
        {
          type: 'category',
          label: 'サーバエラーの管理',
          link: { type: 'doc', id: 'development/managing-server-errors' },
          items: [
            {
              type: 'doc',
              label: 'メッセージ付きの問題',
              id: 'development/problem/problem-with-message',
            },
            {
              type: 'doc',
              label: '制約違反',
              id: 'development/problem/constraint-violation',
            },
            {
              type: 'doc',
              label: 'パラメータ付きメッセージの問題',
              id: 'development/problem/parameterized',
            },
            {
              type: 'doc',
              label: 'エンティティが見つからない',
              id: 'development/problem/entity-not-found',
            },
            {
              type: 'doc',
              label: '無効なパスワード',
              id: 'development/problem/invalid-password',
            },
            {
              type: 'doc',
              label: '既に使用されているメールアドレス',
              id: 'development/problem/email-already-used',
            },
            {
              type: 'doc',
              label: '既に使用されているログイン',
              id: 'development/problem/login-already-used',
            },
            {
              type: 'doc',
              label: 'メールアドレスが見つからない',
              id: 'development/problem/email-not-found',
            },
          ],
        },
        {
          type: 'doc',
          label: 'Angularの使用',
          id: 'development/using-angular',
        },
        { type: 'doc', label: 'Reactの使用', id: 'development/using-react' },
        { type: 'doc', label: 'Vueの使用', id: 'development/using-vue' },
        {
          type: 'doc',
          label: 'Bootstrapのカスタマイズ',
          id: 'development/customizing-bootstrap',
        },
        { type: 'doc', label: 'TLSとHTTP/2の使用', id: 'development/tls' },
      ],
    },
    {
      type: 'category',
      label: 'テストとQA',
      items: [
        {
          type: 'doc',
          label: 'テストの実行',
          id: 'tests-and-qa/running-tests',
        },
        { type: 'doc', label: 'コード品質', id: 'tests-and-qa/code-quality' },
        {
          type: 'doc',
          label: '依存関係の脆弱性チェック',
          id: 'tests-and-qa/dependency-vulnerabities-check',
        },
        {
          type: 'category',
          label: '継続的インテグレーション',
          link: { type: 'doc', id: 'tests-and-qa/setting-up-ci/index' },
          items: [
            {
              type: 'category',
              label: 'Jenkins 1のセットアップ',
              link: {
                type: 'doc',
                id: 'tests-and-qa/setting-up-ci/setting-up-ci-jenkins1',
              },
              items: [
                {
                  type: 'doc',
                  label: 'LinuxでのJenkins 1',
                  id: 'tests-and-qa/setting-up-ci/setting-up-ci-linux',
                },
                {
                  type: 'doc',
                  label: 'WindowsでのJenkins 1',
                  id: 'tests-and-qa/setting-up-ci/setting-up-ci-windows',
                },
              ],
            },
            {
              type: 'doc',
              label: 'Jenkins 2のセットアップ',
              id: 'tests-and-qa/setting-up-ci/setting-up-ci-jenkins2',
            },
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'プロダクション環境',
      items: [
        {
          type: 'doc',
          label: 'プロダクション環境での使用',
          id: 'production/production',
        },
        { type: 'doc', label: 'モニタリング', id: 'production/monitoring' },
        { type: 'doc', label: 'Docker Hub', id: 'production/docker-hub' },
        { type: 'doc', label: 'Azureへのデプロイ', id: 'production/azure' },
        {
          type: 'doc',
          label: 'CloudCaptainを使用したデプロイ',
          id: 'production/cloudcaptain',
        },
        {
          type: 'doc',
          label: 'Clever Cloudへのデプロイ',
          id: 'production/clever-cloud',
        },
        { type: 'doc', label: 'Herokuへのデプロイ', id: 'production/heroku' },
        {
          type: 'doc',
          label: 'Kubernetesへのデプロイ',
          id: 'production/kubernetes',
        },
      ],
    },
    {
      type: 'category',
      label: 'マイクロサービス',
      items: [
        {
          type: 'doc',
          label: '概要',
          id: 'microservices/microservices-architecture',
        },
        { type: 'doc', label: 'APIゲートウェイ', id: 'microservices/api-gateway' },
        { type: 'doc', label: 'Consul', id: 'microservices/consul' },
        {
          type: 'doc',
          label: 'JHipster レジストリ',
          id: 'microservices/jhipster-registry',
        },
        {
          type: 'doc',
          label: 'マイクロサービスの作成',
          id: 'microservices/creating-microservices',
        },
        {
          type: 'doc',
          label: 'プロダクション環境でのマイクロサービス',
          id: 'microservices/microservices-in-production',
        },
        {
          type: 'doc',
          label: 'JHipster コントロールセンター',
          id: 'microservices/jhipster-control-center',
        },
      ],
    },
    {
      type: 'category',
      label: 'Blueprint',
      items: [
        {
          type: 'doc',
          label: '公式Blueprint',
          id: 'modules/official-blueprints',
        },
        {
          type: 'doc',
          label: 'Blueprintの基本',
          id: 'modules/extending-and-customizing',
        },
        {
          type: 'doc',
          label: 'モジュールの作成',
          id: 'modules/creating-a-module',
        },
        {
          type: 'doc',
          label: 'Blueprintの作成',
          id: 'modules/creating-a-blueprint',
        },
        {
          type: 'category',
          label: 'Quarkusドキュメント',
          link: { type: 'doc', id: 'blueprints/quarkus/index' },
          items: [
            {
              type: 'doc',
              label: 'JHipster Quarkus Blueprintのインストール',
              id: 'blueprints/quarkus/installing-jhipster-quarkus',
            },
            {
              type: 'doc',
              label: 'アプリケーションの作成',
              id: 'blueprints/quarkus/creating-an-application',
            },
            {
              type: 'doc',
              label: 'エンティティの作成',
              id: 'blueprints/quarkus/creating-an-entity',
            },
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'ツール',
      items: [
        {
          type: 'link',
          label: 'JDL Studio',
          href: 'https://start.jhipster.tech/jdl-studio/',
        },
        { type: 'doc', label: 'JHipster IDE', id: 'tools/jhipster-ide' },
        { type: 'doc', label: 'JHipster-UML', id: 'tools/jhipster-uml' },
      ],
    },
    {
      type: 'category',
      label: 'JHipsterの概要',
      items: [
        { type: 'doc', label: '技術スタック', id: 'about/tech-stack' },
        {
          type: 'doc',
          label: '5枚のスクリーンショットで見るJHipster',
          id: 'about/screenshots',
        },
        {
          type: 'doc',
          label: 'ビデオチュートリアル（15分）',
          id: 'about/video-tutorial',
        },
        {
          type: 'link',
          label: 'オンラインガイド',
          href: 'https://github.com/jhipster/jhipster-guides',
        },
        {
          type: 'doc',
          label: 'JHipsterを使用する企業',
          id: 'about/companies-using-jhipster',
        },
        {
          type: 'doc',
          label: 'JHipsterアプリのショーケース',
          id: 'about/showcase',
        },
      ],
    },
    {
      type: 'category',
      label: 'リリースノート',
      collapsible: false,
      link: {
        type: 'doc',
        id: 'releases/index',
      },
      items: [{ type: 'autogenerated', dirName: 'releases' }],
    },      
    {
      type: 'category',
      label: 'ヘルプ',
      items: [
        { type: 'doc', label: 'コミュニティのサポート', id: 'help/help' },
        { type: 'doc', label: 'バグ報奨金', id: 'help/bug-bounties' },
      ],
    },
    {
      type: 'category',
      label: 'コントリビュート',
      items: [
        {
          type: 'doc',
          label: 'フィナンシャル・スポンサー',
          id: 'contributing/sponsors',
        },
        {
          type: 'doc',
          label: '個人の支援',
          id: 'contributing/contributing-individuals',
        },
        {
          type: 'doc',
          label: '企業の支援',
          id: 'contributing/contributing-companies',
        },
      ],
    },
    {
      type: 'category',
      label: '開発のヒント',
      link: { type: 'doc', id: 'tips/index' },
      items: [
        {
          type: 'doc',
          label: 'Bootswatchテーマの使用',
          id: 'tips/tips_using_bootswatch_themes',
        },
        {
          type: 'doc',
          label: 'メールを設定する - Gmailなど',
          id: 'tips/tip_configuring_email_in_jhipster',
        },
        {
          type: 'doc',
          label: 'ジェネレータを高速化',
          id: 'tips/tip_speed_up_generator',
        },
        {
          type: 'doc',
          label: 'ローカルSMTPサーバー',
          id: 'tips/tip_local_smtp_server',
        },
        {
          type: 'doc',
          label: 'LDAP認証',
          id: 'tips/tip_ldap_authentication',
        },
        {
          type: 'doc',
          label: 'リモートシェルのREPL (非推奨)',
          id: 'tips/tip_repl_with_the_remote_shell',
        },
        {
          type: 'doc',
          label: 'KubernetesとGoogle Cloud SQL',
          id: 'tips/tip_kubernetes_and_google_cloud_sql',
        },
        {
          type: 'doc',
          label: 'Sliceを使った無限スクロールでページング性能向上',
          id: 'tips/tip_infinite_scroll_with_slice',
        },
        {
          type: 'doc',
          label: 'Mac/WindowsでのDockerコンテナのローカルホスト使用',
          id: 'tips/tip_using_docker_containers_as_localhost_on_mac_and_windows',
        },
        {
          type: 'doc',
          label: 'QueryDSLの使用',
          id: 'tips/tip_add_querydsl_support',
        },
        {
          type: 'doc',
          label: 'Apache (Basic Authentication)でKibanaを保護',
          id: 'tips/tip_protecting_kibana_with_apache_basic_authent',
        },
        {
          type: 'doc',
          label: 'OAuth2によるソーシャルログインの有効化',
          id: 'tips/tip_enabling_social_login_with_oauth2',
        },
        {
          type: 'doc',
          label: '新しい権限の作成',
          id: 'tips/tip_create_new_authority',
        },
        {
          type: 'doc',
          label: '@OneToOneと@MapsIdの問題と回避方法',
          id: 'tips/tip_issue_of_onetoone_with_mapsid_how_to_avoid_it',
        },
        {
          type: 'doc',
          label: '遅延Bean初期化による統合テストの性能向上',
          id: 'tips/tip_lazy_init_test_beans',
        },
        {
          type: 'doc',
          label: 'HerokuにPGAdmin (PostgreSQL)を接続',
          id: 'tips/tip_pgadmin_heroku',
        },
        {
          type: 'doc',
          label: 'Internet Explorerのサポートを提供',
          id: 'tips/tip_ie_support',
        },
        {
          type: 'doc',
          label: 'フロントエンドのみのIDE開発体験の改善',
          id: 'tips/tip_frontend_only',
        },
        {
          type: 'doc',
          label: 'Redisリーダーフォロワー（マスター・スレーブ）レプリケーションの設定',
          id: 'tips/tip_redis_replication',
        },
        {
          type: 'doc',
          label: 'Intellij IDEA内でProtractor e2eテストを実行',
          id: 'tips/tip_e2e_intellij',
        },
        {
          type: 'doc',
          label: 'Dockerでの時間のドリフト',
          id: 'tips/tip_time_drift_docker',
        },
        { type: 'doc', label: 'Userエンティティ管理', id: 'user-entity' },
        {
          type: 'doc',
          label: 'アカウント登録サービスの削除',
          id: 'tips/tip_remove_register_account_service',
        },
        {
          type: 'doc',
          label: 'ジェネレーションとカスタムコードの組み合わせ',
          id: 'tips/tip_combine_generation_and_custom_code',
        },
        {
          type: 'doc',
          label: 'Spring Securityでの一般Webフォントの許可',
          id: 'tips/tip_allow_common_web_fonts_in_spring_security',
        },
      ],
    },
    {
      type: 'doc',
      label: 'JHipster 開発者協会',
      id: 'association',
    },
    {
      type: 'doc',
      label: 'JHipster テックボード',
      id: 'tech-board',
    },
    {
      type: 'doc',
      label: 'JHipster ミートアップ',
      id: 'meetups',
    },
    {
      type: 'doc',
      label: 'アートワーク',
      id: 'artwork',
    },
  ],
};

export default sidebars;
