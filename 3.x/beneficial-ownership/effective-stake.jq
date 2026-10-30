# Effective (indirect) ownership, computed client-side.
# The engine returns the records and the OWNS relationships with their `percent`;
# multiplying stakes along every path is done here, because native SearchQuery
# filters path endpoints and does not compute along a path.
#
# Usage: jq -n -r --slurpfile records R.json --slurpfile rels L.json -f effective-stake.jq
#   R.json: response of queries/03-owners-and-companies.json
#   L.json: response of queries/04-ownership-links.json

($records[0].response.records) as $recs
| ($rels[0].response.relationships) as $links
| ($recs | map({ (.id): .properties }) | add) as $by_id
| ($links | group_by(.targetId) | map({ (.[0].targetId): . }) | add) as $owners_of

# Walk up from company $id, carrying the stake (in percent) and the path so far.
# A path stops when it would revisit a company, so a circular holding contributes
# only its first pass (see README).
| def up($id; $stake; $path; $seen):
    ($owners_of[$id] // [])[] as $r
    | ($stake * $r.properties.percent / 100) as $s
    | ($by_id[$r.sourceId]) as $owner
    | if ($seen | index($r.sourceId)) then empty
      elif $r.sourceLabel == "PERSON" then
        { person: $owner.name, code: $owner.code, sanctioned: $owner.sanctioned,
          stake: $s, path: ([$owner.code] + $path | join(" > ")) }
      else
        up($r.sourceId; $s; [$owner.code] + $path; $seen + [$r.sourceId])
      end;

$recs[]
| select(.label == "COMPANY" and .properties.customer == true)
| .id as $cid | .properties as $c
| "  \($c.code)  \($c.name)",
  ( [ up($cid; 100; [$c.code]; [$cid]) ]
    | group_by(.code)
    | map({ person: .[0].person, sanctioned: .[0].sanctioned,
            stake: (map(.stake) | add), paths: map(.path) })
    | sort_by(-.stake)[]
    | "    \(.person)  \(.stake * 100 | round / 100)%"
      + (if .stake >= 25 then "  beneficial owner (>= 25%)" else "" end)
      + (if .sanctioned then "  SANCTIONED" else "" end)
      + "  via " + (.paths | join(", ")) )
