# Reshape the API export before import:
# - custom_fields is a 1:1 bag of attributes: lift it onto the ticket
# - priority arrives as text or a number: store one type
# - an empty comments array would become a property named like the child label: drop it
map(
  . + .custom_fields | del(.custom_fields)
  | .priority |= (if type == "number" then ({"1":"low","2":"normal","3":"high"}[tostring]) else . end)
  | if .comments == [] then del(.comments) else . end
)
