# Mountfile

Voltgrid.py makes use of a `Mountfile` configuration file to define the writable directories that 
and application has access to.

## Format

The format is as follows:

```
<remote> : <local>
```

Generally the `remote` is a location on shared network storage. And the `local` portion is the local path where the remote will be mounted.

## Examples

For a Django application the following might be used:

```
db : db
www/media : www/media
ephemeral : www/static
```

In this example `ephemeral` defines a mountpoint that will be placed local to the application container.

### Wordpress

A typical Wordpress site would use the following, however additional entries may be required to support certain 3rd party plugins.

```
wp-content/cache: wp-content/cache
wp-content/uploads: wp-content/uploads
```

