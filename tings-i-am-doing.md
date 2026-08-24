log in to databricks

brew trust databricks/tap
brew tap databricks/tap && brew install databricks
databricks auth login --host https://adb-582244602844614.14.azuredatabricks.net (this is just my personal host but could be any other) (after this step a browser window pops up and asks me to allow access)

check that there is billing usage, clusters, active jobs, etc:

SELECT 'billing.usage' AS source, count(*) AS row_count,
       cast(min(usage_date) AS string) AS earliest,
       cast(max(usage_date) AS string) AS latest
FROM system.billing.usage
WHERE usage_date > current_date() - 30
UNION ALL
SELECT 'compute.clusters', count(*),
       cast(min(change_time) AS string), cast(max(change_time) AS string)
FROM system.compute.clusters
UNION ALL
SELECT 'lakeflow.jobs', count(*),
       cast(min(change_time) AS string), cast(max(change_time) AS string)
FROM system.lakeflow.jobs
UNION ALL
SELECT 'query.history', count(*),
       cast(min(start_time) AS string), cast(max(start_time) AS string)
FROM system.query.history
WHERE start_time > current_timestamp() - INTERVAL 30 DAYS
UNION ALL
SELECT 'access.workspaces_latest', count(*),
       cast(min(create_time) AS string), cast(max(create_time) AS string)
FROM system.access.workspaces_latest;

export service principal
export SP=9f87c099-ffc1-4174-97d9-723baf48f5e9

Grant use catalog on DBRX
databricks grants update CATALOG system \
  --json "{\"changes\":[{\"principal\":\"$SP\",\"add\":[\"USE_SCHEMA\",\"SELECT\"]}]}"
{
  "privilege_assignments": [
    {
      "principal": "VergenceContributor",
      "privileges": [
        "APPLY_TAG",
        "BROWSE",
        "MANAGE",
        "READ_VOLUME",
        "SELECT",
        "USE_CATALOG",
        "USE_SCHEMA"
      ]
    },
    {
      "principal": "1a306e1e-d38f-4fc0-a600-c465db07c1fc",
      "privileges": [
        "USE_CATALOG"
      ]
    },
    {
      "principal": "DB - RESERVED - account admins",
      "privileges": [
        "USE_CATALOG"
      ]
    },
    {
      "principal": "casper@vergence.ai",
      "privileges": [
        "MANAGE"
      ]
    },
    {
      "principal": "9f87c099-ffc1-4174-97d9-723baf48f5e9",
      "privileges": [
        "SELECT",
        "USE_CATALOG",
        "USE_SCHEMA"
      ]
    },
    {
      "principal": "account users",
      "privileges": [
        "USE_CATALOG"
      ]
    }
  ]
}

Print client secret id for it to be in environment.local.md

databricks service-principal-secrets-proxy create 142124255918854 --lifetime 7776000s
{
  "create_time": "2026-08-21T14:40:16.000Z",
  "expire_time": "2026-11-19T14:40:16Z",
  "id": "c3c8dae238635ea810aa932fc79f24e5d52909c86430af26cf5d14ff0603b22f",
  "secret": "dose6961970d7ba0687ed95b7e2c0d6571f5",
  "secret_hash": "c3c8dae238635ea810aa932fc79f24e5d52909c86430af26cf5d14ff0603b22f",
  "status": "ACTIVE",
  "update_time": "2026-08-21T14:40:16.000Z"
}