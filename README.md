# Rockcraft SDK for Workshop

This SDK provides Rockcraft for building rocks.
It has the Rockcraft snap with all the tools it bundles.
**This SDK requires `runtime: lxd-vm`; container-based workshops are rejected.**
The Rockcraft cache is persisted on the host to speed up builds across
workshop updates.

---

## Reference workshop

A minimal workshop:

```yaml
# workshop.yaml
name: rocks
base: ubuntu@26.04
runtime: lxd-vm
sdks:
  - name: rockcraft
    channel: "latest/stable"

actions:
  pack: |
    rockcraft pack
```

---

### Using the SDK

#### Prerequisites, project layout

1. Place a `rockcraft.yaml` in your project directory, or create one with
   `rockcraft init`.
2. Use `runtime: lxd-vm` in your `workshop.yaml`. The SDK will take care of
   installing the Rockcraft snap and running
   `lxd init --auto` if the default LXD profile has no root disk, enabling
   Rockcraft's managed build containers inside the VM. If Workshop reports
   that VM support is experimental, enable it on the host with
   `sudo snap set workshop workshop.experimental-vms=1` followed by
   `sudo snap restart workshop.workshopd`.
3. Each clean SDK build resolves Rockcraft's `latest/stable` version and
   architecture-specific snap revision. The SDK adopts that version and
   installs the recorded revision, not whichever revision is stable at launch.
   Automatic Rockcraft snap refreshes are held; update it by updating the SDK.
   Installation still requires the recorded revision to remain downloadable
   from the Snap Store.

#### Build a rock

```bash
workshop run pack
```

The `.rock` file is written to the project directory.

### Explore interactively

```bash
workshop shell
rockcraft --help
```

---

## Plugs (resources this SDK consumes)

### `cache`

- Interface: `mount`
- Workshop target: `/home/workshop/.cache/rockcraft`
- Purpose: Persists the Rockcraft cache between workshop updates.

## Slots (resources this SDK provides)

This SDK doesn't define any slots.

---

## Documentation and guidance

- [Rockcraft documentation](https://documentation.ubuntu.com/rockcraft)

---

## Community and support

- [Rockcraft on GitHub](https://github.com/canonical/rockcraft)
- Please review our [Code of Conduct](https://ubuntu.com/community/ethos/code-of-conduct)
  before participating.

---

## Contributions

All contributions, including code, documentation updates, and issue reports,
are welcome! Open issues or pull requests on the
[official repository](https://github.com/canonical/rockcraft-sdk).

---

## License and copyright

Copyright 2026 Canonical Ltd.

This SDK packages Rockcraft, licensed under the
[GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.html).
