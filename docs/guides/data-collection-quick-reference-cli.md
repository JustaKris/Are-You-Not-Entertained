# Data Collection Quick Reference - CLI Edition

**NOTE: This guide has been superseded by the [CLI Guide](cli-guide.md). Please refer to the CLI Guide for complete and up-to-date documentation.**

For quick reference, here are the most common commands:

## Common Commands

### Initialize Database

```bash
ayne db init
ayne db test
```

### Daily Refresh

```bash
ayne collect daily
ayne collect daily --discover --discover-limit 100
```

### Discover Movies

```bash
# With defaults
ayne tmdb update --max-movies 1000

# Full unlimited discovery
ayne tmdb update --full

# With custom filters
ayne tmdb update --max-movies 5000 --min-year 2020 --min-popularity 15
```

### OMDB Enrichment

```bash
ayne omdb update --max-movies 1000
ayne omdb refresh --limit 200
```

### Validation

```bash
ayne validate all
ayne validate tmdb --verbose
```

## See Also

- **[Complete CLI Guide](cli-guide.md)** - Full documentation with all commands, options, and examples
- **[Data Collection Workflow](../reference/data-collection-workflow.md)** - How the data collection system works
- **[Filtering Configuration](../reference/data-collection-filtering.md)** - Configure filters and limits
