import { readFileSync, existsSync } from 'fs'
import { join } from 'path'
import { parse } from 'csv-parse/sync'

import { APKG } from './index'

// ====== Configuration ======
const ROOT = join(__dirname, '..') // lib/ -> project root
const CSV_PATH = join(ROOT, 'pinyin_word_lookup_filled1.csv')
const MP3_DIR = join(ROOT, 'mp3')

const TONE_COLORS: { [tone: number]: string } = {
  1: '#e33737',
  2: '#e39c37',
  3: '#5cb85c',
  4: '#428bca'
}

// ====== Helpers ======
/** Accent map for every vowel (lower & upper case) and tone (1-4) */
const ACCENTS: { [vowel: string]: string[] } = {
  a: ['ā', 'á', 'ǎ', 'à'],
  e: ['ē', 'é', 'ě', 'è'],
  i: ['ī', 'í', 'ǐ', 'ì'],
  o: ['ō', 'ó', 'ǒ', 'ò'],
  u: ['ū', 'ú', 'ǔ', 'ù'],
  ü: ['ǖ', 'ǘ', 'ǚ', 'ǜ'],
  A: ['Ā', 'Á', 'Ǎ', 'À'],
  E: ['Ē', 'É', 'Ě', 'È'],
  I: ['Ī', 'Í', 'Ǐ', 'Ì'],
  O: ['Ō', 'Ó', 'Ǒ', 'Ò'],
  U: ['Ū', 'Ú', 'Ǔ', 'Ù'],
  Ü: ['Ǖ', 'Ǘ', 'Ǚ', 'Ǜ']
}

/**
 * Convert a syllable with trailing tone number (e.g. "ba4") into pinyin
 * with diacritic plus HTML tone colouring on the main vowel only.
 */
function convertSyllable(raw: string): { plain: string; html: string } {
  const toneDigit = parseInt(raw.slice(-1), 10)
  const base = isNaN(toneDigit) ? raw : raw.slice(0, -1)
  const tone = isNaN(toneDigit) || toneDigit === 0 || toneDigit === 5 ? 0 : toneDigit

  if (tone === 0) {
    return { plain: base, html: base }
  }

  let targetIndex = -1
  const lower = base.toLowerCase()

  // Rule order: a > e > o > (iu/ui) second vowel > last vowel
  if (lower.includes('a')) {
    targetIndex = lower.indexOf('a')
  } else if (lower.includes('e')) {
    targetIndex = lower.indexOf('e')
  } else if (lower.includes('o')) {
    targetIndex = lower.indexOf('o')
  } else if (lower.match(/iu/)) {
    targetIndex = lower.indexOf('u', lower.indexOf('iu'))
  } else if (lower.match(/ui/)) {
    targetIndex = lower.indexOf('i', lower.indexOf('ui'))
  } else {
    // fallback – last vowel in syllable
    const m = [...lower].map((c, idx) => 'aeiouü'.includes(c) ? idx : -1).filter(idx => idx !== -1)
    targetIndex = m.length ? m[m.length - 1] : -1
  }

  if (targetIndex === -1) {
    return { plain: base + toneDigit, html: base + toneDigit }
  }

  const vowel = base[targetIndex]
  const accentSet = ACCENTS[vowel]
  if (!accentSet) {
    // Unexpected vowel char
    return { plain: base + toneDigit, html: base + toneDigit }
  }
  const accented = accentSet[tone - 1]
  const colored = `<span style="color: ${TONE_COLORS[tone]}">${accented}</span>`
  const html = base.slice(0, targetIndex) + colored + base.slice(targetIndex + 1)
  const plain = base.slice(0, targetIndex) + accented + base.slice(targetIndex + 1)
  return { plain, html }
}

function splitMeanings(raw: string): string {
  // Split on forward slash `/` and join with <br>
  return raw.split('/').map(s => s.trim()).join('<br>')
}

// ====== Main ======
if (!existsSync(CSV_PATH)) {
  console.error(`CSV file not found at ${CSV_PATH}`)
  process.exit(1)
}

const csvContent = readFileSync(CSV_PATH, 'utf8')
const records = parse(csvContent, {
  columns: true,
  delimiter: ';',
  skip_empty_lines: true
})

type Row = {
  Syllable: string
  Tone: string
  FullPinyin: string
  Exists: string
  'Character(s)': string
  Meaning: string
  Audio: string
}

const deck1 = new APKG({
  name: 'Pinyin-to-Audio',
  card: {
    fields: ['pinyin', 'audio', 'characters', 'meaning'],
    template: {
      question: '{{pinyin}}',
      answer: `{{pinyin}}<br>{{audio}}<br><b>{{characters}}</b><br>{{meaning}}`
    },
    styleText: `.card { font-family: Arial; font-size: 24px; text-align: center; }`
  }
})

const deck2 = new APKG({
  name: 'Audio-to-Pinyin',
  card: {
    fields: ['audio', 'pinyin', 'characters', 'meaning'],
    template: {
      question: '{{audio}}',
      answer: `{{pinyin}}<br>{{characters}}<br>{{meaning}}`
    },
    styleText: `.card { font-family: Arial; font-size: 24px; text-align: center; }`
  }
})

const mediaCache1 = new Set<string>()
const mediaCache2 = new Set<string>()

records.forEach((row: Row) => {
  if (row.Exists && row.Exists.toLowerCase() !== 'yes') return
  const audioFile = row.Audio?.trim()
  if (!audioFile) return

  const { html: coloredPinyin } = convertSyllable(row.FullPinyin.trim())
  const meaningHtml = splitMeanings(row.Meaning || '')
  const charactersText = row['Character(s)']
  const audioTag = `[sound:${audioFile}]`

  // ----- Deck 1 -----
  deck1.addCard({
    content: [coloredPinyin, audioTag, charactersText, meaningHtml]
  })
  if (!mediaCache1.has(audioFile)) {
    mediaCache1.add(audioFile)
    deck1.addMedia(audioFile, readFileSync(join(MP3_DIR, audioFile)))
  }

  // ----- Deck 2 -----
  deck2.addCard({
    content: [audioTag, coloredPinyin, charactersText, meaningHtml]
  })
  if (!mediaCache2.has(audioFile)) {
    mediaCache2.add(audioFile)
    deck2.addMedia(audioFile, readFileSync(join(MP3_DIR, audioFile)))
  }
})

// Write .apkg files into project root
const OUTPUT_DIR = ROOT

deck1.save(OUTPUT_DIR)
console.log('Generated Pinyin-to-Audio.apkg')

deck2.save(OUTPUT_DIR)
console.log('Generated Audio-to-Pinyin.apkg') 