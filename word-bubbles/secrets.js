/* A secret is a bonus that belongs to the theme, is not a hidden word, and can be
   finished. Pieces of a hidden word (BLOCK inside BLOCKS) are not secrets, and neither
   is a hidden word with more letters stuck on (PUZZLES), because that word locks and
   the bubbles pop before the extra letters can join. */
const WB_SECRETS = {
  "Board games": ["CHESS"],
  "Chemical elements": ["IRON"],
  "Economics": ["DEFLATION"],
  "Feelings": ["ANGRY"],
  "Flowers": ["LILY"],
  "Greek letters": ["GAMMA"],
  "Hobbies": ["HIKING"],
  "Hotel": ["HOTEL"],
  "Pie fillings": ["CRANBERRY"],
  "Ways to cook": ["BASTE"]
};
