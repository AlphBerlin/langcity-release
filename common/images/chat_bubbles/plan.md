# Pixel UI Component Plan

> Requested behavior overrides every placement hint in this report.
> Use Flutter for screen-space layout and Flame/Bonfire for world-space or game-loop behavior.

| Family | Category | Placement hint | Pattern | States | Size | Nine-slice |
|---|---|---|---|---|---:|:---:|
| `bubble_blue_heart` | blue | shared | asset-backed component; choose from requested behavior | default | 48x48 | yes |
| `bubble_blue_octagon` | blue | shared | asset-backed component; choose from requested behavior | default | 48x53 | yes |
| `bubble_blue_pointed` | blue | shared | asset-backed component; choose from requested behavior | default | 48x55 | yes |
| `bubble_blue_right_tail` | blue | shared | asset-backed component; choose from requested behavior | default | 48x53 | yes |
| `bubble_blue_square` | blue | shared | asset-backed component; choose from requested behavior | default | 48x53 | yes |
| `bubble_blue_top_tail` | blue | shared | asset-backed component; choose from requested behavior | default | 48x53 | yes |
| `bubble_blue_top_wide` | blue | shared | asset-backed component; choose from requested behavior | default | 48x21 | yes |
| `bubble_blue_wide` | blue | shared | asset-backed component; choose from requested behavior | default | 48x21 | yes |
| `bubble_mask_heart` | mask | shared | asset-backed component; choose from requested behavior | default | 48x48 | yes |
| `bubble_mask_octagon` | mask | shared | asset-backed component; choose from requested behavior | default | 48x53 | yes |
| `bubble_mask_pointed` | mask | shared | asset-backed component; choose from requested behavior | default | 48x55 | yes |
| `bubble_mask_right_tail` | mask | shared | asset-backed component; choose from requested behavior | default | 48x53 | yes |
| `bubble_mask_square` | mask | shared | asset-backed component; choose from requested behavior | default | 48x53 | yes |
| `bubble_mask_top_tail` | mask | shared | asset-backed component; choose from requested behavior | default | 48x53 | yes |
| `bubble_mask_top_wide` | mask | shared | asset-backed component; choose from requested behavior | default | 48x21 | yes |
| `bubble_mask_wide` | mask | shared | asset-backed component; choose from requested behavior | default | 48x21 | yes |
| `bubble_shadow_heart` | shadow | shared | asset-backed component; choose from requested behavior | default | 53x53 | yes |
| `bubble_shadow_mask_heart` | mask | shared | asset-backed component; choose from requested behavior | default | 52x52 | yes |
| `bubble_shadow_mask_octagon` | mask | shared | asset-backed component; choose from requested behavior | default | 52x57 | yes |
| `bubble_shadow_mask_pointed` | mask | shared | asset-backed component; choose from requested behavior | default | 52x59 | yes |
| `bubble_shadow_mask_right_tail` | mask | shared | asset-backed component; choose from requested behavior | default | 52x57 | yes |
| `bubble_shadow_mask_square` | mask | shared | asset-backed component; choose from requested behavior | default | 52x57 | yes |
| `bubble_shadow_mask_top_tail` | mask | shared | asset-backed component; choose from requested behavior | default | 52x57 | yes |
| `bubble_shadow_mask_wide` | mask | shared | asset-backed component; choose from requested behavior | default | 52x25 | yes |
| `bubble_shadow_octagon` | shadow | shared | asset-backed component; choose from requested behavior | default | 53x58 | yes |
| `bubble_shadow_pointed` | shadow | shared | asset-backed component; choose from requested behavior | default | 52x61 | yes |
| `bubble_shadow_right_tail` | shadow | shared | asset-backed component; choose from requested behavior | default | 53x58 | yes |
| `bubble_shadow_square` | shadow | shared | asset-backed component; choose from requested behavior | default | 53x57 | yes |
| `bubble_shadow_top_tail` | shadow | shared | asset-backed component; choose from requested behavior | default | 54x59 | yes |
| `bubble_shadow_top_wide` | shadow | shared | asset-backed component; choose from requested behavior | default | 53x27 | yes |
| `bubble_shadow_wide` | shadow | shared | asset-backed component; choose from requested behavior | default | 53x26 | yes |

## Placement review

Resolve every `shared` family from the requested behavior before implementation. 
A minimap marker is normally Flutter overlay UI; a marker following a world object is normally a Flame/Bonfire component or a camera-projected Flutter overlay.
