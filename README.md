# Oppo UDP-20x

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

Home Assistant integration for Oppo UDP-20x Blu-ray players (UDP-203 / UDP-205).

> **Maintained fork.** This is an actively-maintained continuation of
> [`simbaja/ha_oppoudp`](https://github.com/simbaja/ha_oppoudp) by Jack Simbach,
> which is no longer receiving updates. The integration domain is unchanged
> (`oppo_udp`), so it installs as a drop-in replacement — existing entities,
> history, and automations are preserved.

## Installation (HACS)

1. Add this repository as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/)
   in HACS, using `https://github.com/eklundjon/ha-oppoudp` as the URL and
   **Integration** as the category.
2. Install "Oppo UDP-20x" and restart Home Assistant.
3. In the HA UI go to **Settings → Devices & Services → Add Integration** and
   search for "Oppo UDP".

## Installation (Manual)

1. Open the directory (folder) for your HA configuration (where `configuration.yaml` lives).
2. Create a `custom_components` directory there if you don't have one.
3. Copy the `custom_components/oppo_udp/` folder from this repository into it.
4. Restart Home Assistant.
5. Add the integration as described above.

## Configuration

Configuration is done via the Home Assistant UI.

### Notes

1. The Oppo UDP must be **ON** during setup so it can pass the connection test.
2. Set the player's standby mode to **"Network Standby"** so it stays reachable
   while powered off.
3. If the player's IP address changes, use the integration's **Reconfigure**
   option to update it without deleting and re-adding the device.

## Credits

Originally created by [Jack Simbach](https://github.com/simbaja)
([`simbaja/ha_oppoudp`](https://github.com/simbaja/ha_oppoudp)). Licensed under MIT.

[commits-shield]: https://img.shields.io/github/commit-activity/y/eklundjon/ha-oppoudp.svg?style=for-the-badge
[commits]: https://github.com/eklundjon/ha-oppoudp/commits/master
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/eklundjon/ha-oppoudp.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40eklundjon-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/eklundjon/ha-oppoudp.svg?style=for-the-badge
[releases]: https://github.com/eklundjon/ha-oppoudp/releases
