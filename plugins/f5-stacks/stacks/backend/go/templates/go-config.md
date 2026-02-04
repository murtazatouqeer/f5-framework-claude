# Go Config Template

Template for application configuration in Go applications.

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{app_name}}` | Application name | myproject |
| `{{module_path}}` | Go module path | myproject |

## Config Structure Template

```go
// internal/config/config.go
package config

import (
    "fmt"
    "time"

    "github.com/spf13/viper"
)

type Config struct {
    App      AppConfig      `mapstructure:"app"`
    Server   ServerConfig   `mapstructure:"server"`
    Database DatabaseConfig `mapstructure:"database"`
    Redis    RedisConfig    `mapstructure:"redis"`
    JWT      JWTConfig      `mapstructure:"jwt"`
    Log      LogConfig      `mapstructure:"log"`
    {{#additional_configs}}
    {{config_name}} {{config_type}} `mapstructure:"{{config_key}}"`
    {{/additional_configs}}
}

type AppConfig struct {
    Name        string `mapstructure:"name"`
    Version     string `mapstructure:"version"`
    Environment string `mapstructure:"environment"`
    Debug       bool   `mapstructure:"debug"`
}

type ServerConfig struct {
    Host            string        `mapstructure:"host"`
    Port            int           `mapstructure:"port"`
    ReadTimeout     time.Duration `mapstructure:"read_timeout"`
    WriteTimeout    time.Duration `mapstructure:"write_timeout"`
    ShutdownTimeout time.Duration `mapstructure:"shutdown_timeout"`
}

type DatabaseConfig struct {
    Host            string        `mapstructure:"host"`
    Port            int           `mapstructure:"port"`
    User            string        `mapstructure:"user"`
    Password        string        `mapstructure:"password"`
    DBName          string        `mapstructure:"dbname"`
    SSLMode         string        `mapstructure:"sslmode"`
    MaxOpenConns    int           `mapstructure:"max_open_conns"`
    MaxIdleConns    int           `mapstructure:"max_idle_conns"`
    ConnMaxLifetime time.Duration `mapstructure:"conn_max_lifetime"`
}

func (c *DatabaseConfig) DSN() string {
    return fmt.Sprintf(
        "host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
        c.Host, c.Port, c.User, c.Password, c.DBName, c.SSLMode,
    )
}

type RedisConfig struct {
    Host     string `mapstructure:"host"`
    Port     int    `mapstructure:"port"`
    Password string `mapstructure:"password"`
    DB       int    `mapstructure:"db"`
}

func (c *RedisConfig) Addr() string {
    return fmt.Sprintf("%s:%d", c.Host, c.Port)
}

type JWTConfig struct {
    SecretKey     string        `mapstructure:"secret_key"`
    AccessExpiry  time.Duration `mapstructure:"access_expiry"`
    RefreshExpiry time.Duration `mapstructure:"refresh_expiry"`
    Issuer        string        `mapstructure:"issuer"`
}

type LogConfig struct {
    Level      string `mapstructure:"level"`
    Format     string `mapstructure:"format"`
    OutputPath string `mapstructure:"output_path"`
}

func (c *ServerConfig) Addr() string {
    return fmt.Sprintf("%s:%d", c.Host, c.Port)
}

func (c *AppConfig) IsProduction() bool {
    return c.Environment == "production"
}

func (c *AppConfig) IsDevelopment() bool {
    return c.Environment == "development"
}
```

## Config Loader Template

```go
// internal/config/loader.go
package config

import (
    "fmt"
    "strings"

    "github.com/spf13/viper"
)

func Load(configPath string) (*Config, error) {
    v := viper.New()

    // Set config file
    if configPath != "" {
        v.SetConfigFile(configPath)
    } else {
        v.SetConfigName("config")
        v.SetConfigType("yaml")
        v.AddConfigPath(".")
        v.AddConfigPath("./config")
        v.AddConfigPath("/etc/{{app_name}}")
    }

    // Environment variables
    v.SetEnvPrefix("{{APP_PREFIX}}")
    v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
    v.AutomaticEnv()

    // Set defaults
    setDefaults(v)

    // Read config file
    if err := v.ReadInConfig(); err != nil {
        if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
            return nil, fmt.Errorf("reading config file: %w", err)
        }
    }

    var cfg Config
    if err := v.Unmarshal(&cfg); err != nil {
        return nil, fmt.Errorf("unmarshaling config: %w", err)
    }

    if err := cfg.Validate(); err != nil {
        return nil, fmt.Errorf("validating config: %w", err)
    }

    return &cfg, nil
}

func setDefaults(v *viper.Viper) {
    // App defaults
    v.SetDefault("app.name", "{{app_name}}")
    v.SetDefault("app.version", "1.0.0")
    v.SetDefault("app.environment", "development")
    v.SetDefault("app.debug", true)

    // Server defaults
    v.SetDefault("server.host", "0.0.0.0")
    v.SetDefault("server.port", 8080)
    v.SetDefault("server.read_timeout", "30s")
    v.SetDefault("server.write_timeout", "30s")
    v.SetDefault("server.shutdown_timeout", "30s")

    // Database defaults
    v.SetDefault("database.host", "localhost")
    v.SetDefault("database.port", 5432)
    v.SetDefault("database.user", "postgres")
    v.SetDefault("database.password", "")
    v.SetDefault("database.dbname", "{{app_name}}")
    v.SetDefault("database.sslmode", "disable")
    v.SetDefault("database.max_open_conns", 25)
    v.SetDefault("database.max_idle_conns", 25)
    v.SetDefault("database.conn_max_lifetime", "5m")

    // Redis defaults
    v.SetDefault("redis.host", "localhost")
    v.SetDefault("redis.port", 6379)
    v.SetDefault("redis.password", "")
    v.SetDefault("redis.db", 0)

    // JWT defaults
    v.SetDefault("jwt.secret_key", "your-secret-key-change-in-production")
    v.SetDefault("jwt.access_expiry", "15m")
    v.SetDefault("jwt.refresh_expiry", "7d")
    v.SetDefault("jwt.issuer", "{{app_name}}")

    // Log defaults
    v.SetDefault("log.level", "info")
    v.SetDefault("log.format", "json")
    v.SetDefault("log.output_path", "stdout")
}

func (c *Config) Validate() error {
    if c.App.Name == "" {
        return fmt.Errorf("app.name is required")
    }
    if c.JWT.SecretKey == "" || c.JWT.SecretKey == "your-secret-key-change-in-production" {
        if c.App.IsProduction() {
            return fmt.Errorf("jwt.secret_key must be set in production")
        }
    }
    return nil
}
```

## YAML Config Template

```yaml
# config/config.yaml
app:
  name: {{app_name}}
  version: 1.0.0
  environment: development
  debug: true

server:
  host: 0.0.0.0
  port: 8080
  read_timeout: 30s
  write_timeout: 30s
  shutdown_timeout: 30s

database:
  host: localhost
  port: 5432
  user: postgres
  password: secret
  dbname: {{app_name}}
  sslmode: disable
  max_open_conns: 25
  max_idle_conns: 25
  conn_max_lifetime: 5m

redis:
  host: localhost
  port: 6379
  password: ""
  db: 0

jwt:
  secret_key: your-super-secret-key-change-in-production
  access_expiry: 15m
  refresh_expiry: 168h  # 7 days
  issuer: {{app_name}}

log:
  level: info
  format: json
  output_path: stdout
```

## Environment File Template

```env
# .env.example

# App
APP_NAME={{app_name}}
APP_VERSION=1.0.0
APP_ENVIRONMENT=development
APP_DEBUG=true

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
SERVER_READ_TIMEOUT=30s
SERVER_WRITE_TIMEOUT=30s
SERVER_SHUTDOWN_TIMEOUT=30s

# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=secret
DATABASE_DBNAME={{app_name}}
DATABASE_SSLMODE=disable
DATABASE_MAX_OPEN_CONNS=25
DATABASE_MAX_IDLE_CONNS=25
DATABASE_CONN_MAX_LIFETIME=5m

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# JWT
JWT_SECRET_KEY=your-super-secret-key
JWT_ACCESS_EXPIRY=15m
JWT_REFRESH_EXPIRY=168h
JWT_ISSUER={{app_name}}

# Log
LOG_LEVEL=info
LOG_FORMAT=json
LOG_OUTPUT_PATH=stdout
```

## Usage

```bash
# Generate config with custom sections
f5 generate config --app-name myproject \
  --sections "smtp,s3,stripe"
```
