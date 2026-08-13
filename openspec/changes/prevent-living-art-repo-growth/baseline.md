# Living-art baseline

The reachable-history baseline was measured from `main` at
`8bc966e804a84330cd450c4f9d2f7a1bce4e8cfa` on 2026-08-12. Current-fleet media
measurements come from the post-change manifest-v2 and checked-in GIFs in the
working tree. This is not an encoder benchmark or an external-storage cost
estimate.

## Reachable history

`git count-objects -vH` reported a 5.28 GiB pack. To avoid double-counting the
repository and docs mirrors, reachable living-art objects were deduplicated by
object ID before their uncompressed blob sizes were summed:

```bash
git rev-list --objects --all -- \
  '.github/assets/img/living-*.gif' \
  'docs/public/showcase/living-*.gif' \
  | awk '{print $1}' | sort -u > living-art-object-ids.txt
git cat-file --batch-check='%(objectname) %(objecttype) %(objectsize)' \
  < living-art-object-ids.txt
```

The result was 337 unique reachable GIF blobs totaling 2,373,159,009 bytes
(2.210177 GiB). This is historical evidence only: the change does not rewrite
history or delete reachable objects.

## Checked-in fleet

The manifest-v2 descriptors are the source of truth for per-asset dimensions,
frames, playback duration, loop behavior, byte count, and SHA-256. The six
current repository assets total 20,665,377 bytes and are all 400 x 400 pixels.
Their frame counts are 89, 91, 98, 103, 98, and 118 (range 89-118); playback
durations range from 29,660 ms to 29,730 ms. The repository and docs-showcase
copies are byte-identical.

Reproduce the current measurement with:

```bash
jq '{manifest_version,total_assets,total_bytes,assets:[.assets[] |
  {name,bytes,width,height,frames,duration_ms,loop,sha256}]}' \
  .github/assets/img/living-art-manifest.json
```
