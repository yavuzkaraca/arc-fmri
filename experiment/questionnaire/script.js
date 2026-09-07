// Define study
const study = lab.util.fromObject({
  "title": "root",
  "type": "lab.flow.Sequence",
  "parameters": {},
  "plugins": [
    {
      "type": "lab.plugins.Metadata",
      "path": undefined
    },
    {
      "type": "lab.plugins.Download",
      "filePrefix": "arc-like-task-test",
      "path": undefined
    }
  ],
  "metadata": {
    "title": "Arc-like Task Test",
    "description": "",
    "repository": "",
    "contributors": "Yavuz Karaca \u003Cyavkaraca@gmail.com\u003E"
  },
  "files": {},
  "responses": {},
  "content": [
    {
      "type": "lab.html.Form",
      "content": "\u003Cform\u003E\n  \u003Csection class=\"survey-section\"\u003E\n    \u003Ch2\u003EParticipant Information\u003C\u002Fh2\u003E\n\n    \u003Cdiv class=\"meta-grid\"\u003E\n      \u003Clabel class=\"field\"\u003E\n        \u003Cspan\u003EParticipant ID\u003C\u002Fspan\u003E\n        \u003Cinput\n          autocomplete=\"off\"\n          id=\"participant_id\"\n          name=\"participant_id\"\n          type=\"text\"\n          inputmode=\"numeric\"\n          maxlength=\"3\"\n          pattern=\"p[0-9]{2}\"\n          placeholder=\"p01\"\n          required\n          oninput=\"\n            const digits = this.value.replace(\u002F\\D\u002Fg, '').slice(0, 2);\n            this.value = 'p' + digits;\n          \"\n        \u003E\n      \u003C\u002Flabel\u003E\n\n      \u003Clabel class=\"field\"\u003E\n        \u003Cspan\u003EDate\u003C\u002Fspan\u003E\n        \u003Cinput\n          id=\"survey_date\"\n          name=\"survey_date\"\n          type=\"date\"\n          min=\"2026-01-01\"\n          max=\"2198-12-31\"\n          required\n        \u003E\n      \u003C\u002Flabel\u003E\n    \u003C\u002Fdiv\u003E\n\n    \u003Cdiv class=\"form-actions\"\u003E\n      \u003Cbutton type=\"submit\"\u003ENext\u003C\u002Fbutton\u003E\n    \u003C\u002Fdiv\u003E\n  \u003C\u002Fsection\u003E\n\u003C\u002Fform\u003E",
      "scrollTop": true,
      "files": {},
      "responses": {
        "": ""
      },
      "parameters": {},
      "messageHandlers": {},
      "title": "1. Participant Information"
    },
    {
      "type": "lab.html.Form",
      "content": "\u003Cform\u003E\n  \u003Csection class=\"survey-section\"\u003E\n    \u003Ch2\u003EGeneral Strategy\u003C\u002Fh2\u003E\n\n    \u003Cdiv class=\"question\"\u003E\n      \u003Clabel for=\"A1\"\u003E\n        \u003Cstrong\u003E\n          Did you use a specific strategy to work out the rule shown in a pair of images? Could you describe your strategy?\n        \u003C\u002Fstrong\u003E\n      \u003C\u002Flabel\u003E\n\n      \u003Ctextarea\n        class=\"text-answer\"\n        id=\"A1\"\n        name=\"A1\"\n        rows=\"5\"\n        required\n      \u003E\u003C\u002Ftextarea\u003E\n    \u003C\u002Fdiv\u003E\n\n    \u003Cdiv class=\"question\"\u003E\n      \u003Clabel for=\"A2\"\u003E\n        \u003Cstrong\u003E\n          Did your strategy differ between the two kinds of blocks? If so, could you describe in what way your strategies differed?\n        \u003C\u002Fstrong\u003E\n\n        \u003Cspan class=\"question-note\"\u003E\n          Comparing to the previous pair vs. the memorized first pair.\n        \u003C\u002Fspan\u003E\n      \u003C\u002Flabel\u003E\n\n      \u003Ctextarea\n        class=\"text-answer\"\n        id=\"A2\"\n        name=\"A2\"\n        rows=\"5\"\n        required\n      \u003E\u003C\u002Ftextarea\u003E\n    \u003C\u002Fdiv\u003E\n\n    \u003Cdiv class=\"question\"\u003E\n      \u003Clabel for=\"A3\"\u003E\n        \u003Cstrong\u003E\n          Which of these two kinds of blocks felt easier, and why?\n        \u003C\u002Fstrong\u003E\n      \u003C\u002Flabel\u003E\n\n      \u003Ctextarea\n        class=\"text-answer\"\n        id=\"A3\"\n        name=\"A3\"\n        rows=\"5\"\n        required\n      \u003E\u003C\u002Ftextarea\u003E\n    \u003C\u002Fdiv\u003E\n\n    \u003Cdiv class=\"form-actions\"\u003E\n      \u003Cbutton type=\"submit\"\u003ENext\u003C\u002Fbutton\u003E\n    \u003C\u002Fdiv\u003E\n  \u003C\u002Fsection\u003E\n\u003C\u002Fform\u003E",
      "scrollTop": true,
      "files": {},
      "responses": {
        "": ""
      },
      "parameters": {},
      "messageHandlers": {},
      "title": "2. General Strategy"
    },
    {
      "type": "lab.html.Form",
      "content": "\u003Cform\u003E\n  \u003Csection class=\"survey-section\"\u003E\n    \u003Ch2\u003ERule Descriptions\u003C\u002Fh2\u003E\n\n    \u003Cp class=\"section-intro\"\u003E\n      In the following section, you will see several examples of the rules from the experiment.\n    \u003C\u002Fp\u003E\n\n    \u003Cp class=\"section-intro\" style=\"margin-top: 18px;\"\u003E\n      For each example, identify the underlying rule. Then describe it in your own words as if you had to explain the correct rule to someone who is unfamiliar with the task.\n    \u003C\u002Fp\u003E\n\n    \u003Cinput type=\"hidden\" name=\"part_b_intro_seen\" value=\"1\"\u003E\n\n    \u003Cdiv class=\"form-actions\"\u003E\n      \u003Cbutton type=\"submit\"\u003ENext\u003C\u002Fbutton\u003E\n    \u003C\u002Fdiv\u003E\n  \u003C\u002Fsection\u003E\n\u003C\u002Fform\u003E",
      "scrollTop": true,
      "files": {},
      "responses": {
        "": ""
      },
      "parameters": {},
      "messageHandlers": {},
      "title": "3. Rule Descriptions - Intro"
    },
    {
      "type": "lab.flow.Loop",
      "templateParameters": [],
      "sample": {
        "mode": "sequential"
      },
      "files": {},
      "responses": {
        "": ""
      },
      "parameters": {},
      "messageHandlers": {
        "before:prepare": function anonymous(
) {
const rules = [
  // Arithmetic
  { id: 'B_ARI_equalize_colors', image: 'arithmetic.equalize_colors' },
  { id: 'B_ARI_increment_majority_color', image: 'arithmetic.increment_majority_color' },
  { id: 'B_ARI_increment_minority_color', image: 'arithmetic.increment_minority_color' },

  // Attraction
  { id: 'B_ATT_color_attraction', image: 'attraction.color_attraction' },
  { id: 'B_ATT_size_attraction', image: 'attraction.size_attraction' },
  { id: 'B_ATT_color_repulsion', image: 'attraction.color_repulsion' },
  { id: 'B_ATT_floating_blocks', image: 'attraction.floating_blocks' },
  { id: 'B_ATT_falling_blocks', image: 'attraction.falling_blocks' },

  // Recoloring
  { id: 'B_REB_color_inversion', image: 'recolor.color_inversion' },
  { id: 'B_REB_shape_color_mapping', image: 'recolor.shape_color_mapping' },
  { id: 'B_REB_touching_edges_recolor', image: 'recolor.touching_edges_recolor' },

  // Expansion
  { id: 'B_EXP_plus_step', image: 'expansion.plus_step' },
  { id: 'B_EXP_plus_ray', image: 'expansion.plus_ray' },
  { id: 'B_EXP_star_step', image: 'expansion.star_step' },
  { id: 'B_EXP_star_ray', image: 'expansion.star_ray' },
  { id: 'B_EXP_3_arm_star_ray', image: 'expansion.3_arm_star_ray' },

  // Occlusion
  { id: 'B_OCB_occlusion_reversal', image: 'occlusion.occlusion_reversal' },
  { id: 'B_OCB_mirror_x', image: 'occlusion.mirror_x' },
  { id: 'B_OCB_mirror_y', image: 'occlusion.mirror_y' },
  { id: 'B_OCB_rotate_180', image: 'occlusion.rotate_180' },
  { id: 'B_OCB_rotate_90', image: 'occlusion.rotate_90' }
]

const shuffled = this.random.shuffle(rules)
const pageSizes = [4, 4, 4, 4, 5]

this.options.templateParameters = []

let index = 0

for (let page = 0; page < pageSizes.length; page++) {
  const r = shuffled.slice(index, index + pageSizes[page])
  index += pageSizes[page]

  // On pages 1–4 use q4 as a harmless hidden fallback for q5.
  const q5 = r[4] || r[3]

  this.options.templateParameters.push({
    page: page + 1,
    has_q5: Boolean(r[4]),

    q1_id: r[0].id,
    q1_img1: `${r[0].image}.t1.combined.png`,
    q1_img2: `${r[0].image}.t2.combined.png`,

    q2_id: r[1].id,
    q2_img1: `${r[1].image}.t1.combined.png`,
    q2_img2: `${r[1].image}.t2.combined.png`,

    q3_id: r[2].id,
    q3_img1: `${r[2].image}.t1.combined.png`,
    q3_img2: `${r[2].image}.t2.combined.png`,

    q4_id: r[3].id,
    q4_img1: `${r[3].image}.t1.combined.png`,
    q4_img2: `${r[3].image}.t2.combined.png`,

    q5_id: r[4] ? r[4].id : '_unused_q5',
    q5_img1: `${q5.image}.t1.combined.png`,
    q5_img2: `${q5.image}.t2.combined.png`
  })
}
}
      },
      "title": "Loop",
      "shuffleGroups": [],
      "template": {
        "type": "lab.html.Form",
        "content": "\u003Cform\u003E\n  \u003Csection class=\"survey-section\"\u003E\n    \u003Ch2\u003ERule Descriptions\u003C\u002Fh2\u003E\n\n    \u003Cdiv class=\"rule-question\"\u003E\n      \u003Cdiv class=\"stimulus-pair\"\u003E\n        \u003Cimg\n          alt=\"Rule example 1\"\n          src=\"${this.files[parameters.q1_img1]}\"\n        \u003E\n        \u003Cimg\n          alt=\"Rule example 2\"\n          src=\"${this.files[parameters.q1_img2]}\"\n        \u003E\n      \u003C\u002Fdiv\u003E\n\n      \u003Clabel for=\"${parameters.q1_id}\"\u003EDescribe the rule:\u003C\u002Flabel\u003E\n      \u003Ctextarea\n        class=\"text-answer rule-answer\"\n        id=\"${parameters.q1_id}\"\n        name=\"${parameters.q1_id}\"\n        rows=\"4\"\n        required\n      \u003E\u003C\u002Ftextarea\u003E\n    \u003C\u002Fdiv\u003E\n\n    \u003Cdiv class=\"rule-question\"\u003E\n      \u003Cdiv class=\"stimulus-pair\"\u003E\n        \u003Cimg\n          alt=\"Rule example 1\"\n          src=\"${this.files[parameters.q2_img1]}\"\n        \u003E\n        \u003Cimg\n          alt=\"Rule example 2\"\n          src=\"${this.files[parameters.q2_img2]}\"\n        \u003E\n      \u003C\u002Fdiv\u003E\n\n      \u003Clabel for=\"${parameters.q2_id}\"\u003EDescribe the rule:\u003C\u002Flabel\u003E\n      \u003Ctextarea\n        class=\"text-answer rule-answer\"\n        id=\"${parameters.q2_id}\"\n        name=\"${parameters.q2_id}\"\n        rows=\"4\"\n        required\n      \u003E\u003C\u002Ftextarea\u003E\n    \u003C\u002Fdiv\u003E\n\n    \u003Cdiv class=\"rule-question\"\u003E\n      \u003Cdiv class=\"stimulus-pair\"\u003E\n        \u003Cimg\n          alt=\"Rule example 1\"\n          src=\"${this.files[parameters.q3_img1]}\"\n        \u003E\n        \u003Cimg\n          alt=\"Rule example 2\"\n          src=\"${this.files[parameters.q3_img2]}\"\n        \u003E\n      \u003C\u002Fdiv\u003E\n\n      \u003Clabel for=\"${parameters.q3_id}\"\u003EDescribe the rule:\u003C\u002Flabel\u003E\n      \u003Ctextarea\n        class=\"text-answer rule-answer\"\n        id=\"${parameters.q3_id}\"\n        name=\"${parameters.q3_id}\"\n        rows=\"4\"\n        required\n      \u003E\u003C\u002Ftextarea\u003E\n    \u003C\u002Fdiv\u003E\n\n    \u003Cdiv class=\"rule-question\"\u003E\n      \u003Cdiv class=\"stimulus-pair\"\u003E\n        \u003Cimg\n          alt=\"Rule example 1\"\n          src=\"${this.files[parameters.q4_img1]}\"\n        \u003E\n        \u003Cimg\n          alt=\"Rule example 2\"\n          src=\"${this.files[parameters.q4_img2]}\"\n        \u003E\n      \u003C\u002Fdiv\u003E\n\n      \u003Clabel for=\"${parameters.q4_id}\"\u003EDescribe the rule:\u003C\u002Flabel\u003E\n      \u003Ctextarea\n        class=\"text-answer rule-answer\"\n        id=\"${parameters.q4_id}\"\n        name=\"${parameters.q4_id}\"\n        rows=\"4\"\n        required\n      \u003E\u003C\u002Ftextarea\u003E\n    \u003C\u002Fdiv\u003E\n\n    \u003Cdiv\n      class=\"rule-question\"\n      style=\"${parameters.has_q5 ? '' : 'display: none;'}\"\n    \u003E\n      \u003Cdiv class=\"stimulus-pair\"\u003E\n        \u003Cimg\n          alt=\"Rule example 1\"\n          src=\"${this.files[parameters.q5_img1]}\"\n        \u003E\n        \u003Cimg\n          alt=\"Rule example 2\"\n          src=\"${this.files[parameters.q5_img2]}\"\n        \u003E\n      \u003C\u002Fdiv\u003E\n\n      \u003Clabel for=\"${parameters.q5_id}\"\u003EDescribe the rule:\u003C\u002Flabel\u003E\n      \u003Ctextarea\n        class=\"text-answer rule-answer\"\n        id=\"${parameters.q5_id}\"\n        name=\"${parameters.q5_id}\"\n        rows=\"4\"\n        ${parameters.has_q5 ? 'required' : 'disabled'}\n      \u003E\u003C\u002Ftextarea\u003E\n    \u003C\u002Fdiv\u003E\n\n    \u003Cdiv class=\"form-actions\"\u003E\n      \u003Cbutton type=\"submit\"\u003E\n        ${parameters.page === 5 ? 'Finish questionnaire' : 'Next'}\n      \u003C\u002Fbutton\u003E\n    \u003C\u002Fdiv\u003E\n  \u003C\u002Fsection\u003E\n\u003C\u002Fform\u003E",
        "scrollTop": true,
        "files": {
          "arithmetic.equalize_colors.t1.combined.png": "embedded\u002F69f0e5d46b75089a06a93d7bf2eb48c1b316824012693f14d08a31278c54f381.png",
          "arithmetic.equalize_colors.t2.combined.png": "embedded\u002Fb0aadee493e8fb6aece935ac2ef45a9f9310a163df546786094771002a8590f7.png",
          "arithmetic.increment_majority_color.t1.combined.png": "embedded\u002F499ba3a077debf914286333ca04f1c8579ed5c2acb58ae50c0deef291c9a496c.png",
          "arithmetic.increment_majority_color.t2.combined.png": "embedded\u002F33824b8076076d599b45c3f6edd601488b08174644a885dc1d595776a701eead.png",
          "arithmetic.increment_minority_color.t1.combined.png": "embedded\u002F24a7f57624789bd384db8c31e4d4ce7f89f5538009badf64ff934e561d8270e6.png",
          "arithmetic.increment_minority_color.t2.combined.png": "embedded\u002F06de5916bd33ceab67d4b39e6dcb113a6c1ed9c769ffedd831253becebd051c0.png",
          "attraction.color_attraction.t1.combined.png": "embedded\u002Fa5e515df0835222858b213319986ae119e1767286dc1a131455b66c85743e944.png",
          "attraction.color_attraction.t2.combined.png": "embedded\u002F21afe9decf236b4865fd437058bf4d6f302a6c6743a54ebb3f744787fffdf8fd.png",
          "attraction.color_repulsion.t1.combined.png": "embedded\u002Fe996e5de59ad6188ee319b8247add6756f7de55ea51ee39ad869468261c55b87.png",
          "attraction.color_repulsion.t2.combined.png": "embedded\u002F47e5876c577236df220105e28984688bffc13fd15106095bc7a5d1a939e152c9.png",
          "attraction.falling_blocks.t1.combined.png": "embedded\u002F09668a652d0533ecb9b4a672205c9cba01366191d989bd96c55d7f775cb81cc2.png",
          "attraction.falling_blocks.t2.combined.png": "embedded\u002Fcb44dd114afda986bd477b7f0bc0ea661d22bcdb5056780eb71c69a1cb7eff29.png",
          "attraction.floating_blocks.t1.combined.png": "embedded\u002F7a7050a05d8ad60c3b59b3517960491b3d5b62f14333b33c716096e322f53496.png",
          "attraction.floating_blocks.t2.combined.png": "embedded\u002F14fd56fd63fb36f03e0a88c6629fbab6f65e63b21648ca2a18cb433b6d2b5b16.png",
          "attraction.size_attraction.t1.combined.png": "embedded\u002F29283e244922d84436bf011706115cb8bcb2b4d34c37f0d19beb3828ddc0931d.png",
          "attraction.size_attraction.t2.combined.png": "embedded\u002Ff31c471d616217fd661eab05c9598e947c12f27af4e6310deac5f1fd21db345f.png",
          "expansion.3_arm_star_ray.t1.combined.png": "embedded\u002F20bd633059f494cd9cf8ccbabc43dc2133a63fd7558356ce1053a82b9dc13a29.png",
          "expansion.3_arm_star_ray.t2.combined.png": "embedded\u002F4898013db0bf3e45533ef61cb6d95e3bd45eb20bb33984443956afe744e4d90f.png",
          "expansion.plus_ray.t1.combined.png": "embedded\u002Fd38d8a767d5e71379e256da506d77c8ab3f85f7738b4f0de981f198ae8b41fb7.png",
          "expansion.plus_ray.t2.combined.png": "embedded\u002F0e532e53d55760c56d7ca9ca7b325c05d3221fc619c418de5b909a4a216e85eb.png",
          "expansion.plus_step.t1.combined.png": "embedded\u002F5caffaa2e663a3f780719fb80d6459d33845c8377e74b874ae7085d370ef4577.png",
          "expansion.plus_step.t2.combined.png": "embedded\u002F7af67cf6ad2658201938c24dde40e5295b22e5c6ed3617c4db7c1403e8d39a26.png",
          "expansion.star_ray.t1.combined.png": "embedded\u002Fcd37aa86f3cb69668e1a207be8564ba2440934d25d11ba37468277db580a5403.png",
          "expansion.star_ray.t2.combined.png": "embedded\u002Fbe9881fdc57070b4556f351cdf4cfd3d6347b05a5cf6db93b797dd74e52e68d7.png",
          "expansion.star_step.t1.combined.png": "embedded\u002Ff35ef2e9d56f6462d5411b456f9f2aac75437942867fcfd6551f72cba3701473.png",
          "expansion.star_step.t2.combined.png": "embedded\u002F983212ca41f84ff2fc95f512bc3214a0efe89a6e5d09ffd0d31efde31e92319d.png",
          "occlusion.mirror_x.t1.combined.png": "embedded\u002Fcb29d6de890613f0e66db6346cc95821760f875dd39d7ad49ce8d5a78f68bd16.png",
          "occlusion.mirror_x.t2.combined.png": "embedded\u002F21f6759d3126ba90aa8c778bfeeaf84cd0c14ccbb7c5334c92c39bff90b27b30.png",
          "occlusion.mirror_y.t1.combined.png": "embedded\u002Fd0f5a77fdea896ba45af1851a0c3687b504d55c89c386deac693c46d9bfab69c.png",
          "occlusion.mirror_y.t2.combined.png": "embedded\u002F1dc8632f747a46891dd4781ce9e3539288d2e9adf247465e9db0a4d39f8e4715.png",
          "occlusion.occlusion_reversal.t1.combined.png": "embedded\u002F4c47671eecb18c9a5fd00591d3e15050cebd03a762d76dc27407b847404b9be8.png",
          "occlusion.occlusion_reversal.t2.combined.png": "embedded\u002F822c7041195e343ef358eb8da42c99c01dbb6171c8871bfecefc113928d4ae3f.png",
          "occlusion.rotate_90.t1.combined.png": "embedded\u002Ff54dd7fe10ecd64d918061bcae81c0d28867a93925ab17f309b7151648020e8c.png",
          "occlusion.rotate_90.t2.combined.png": "embedded\u002Fc6dfdd8c69309bcd14b88fa5b0bd414957ed1c20a0d1ed627b2d686d7b75eb1c.png",
          "occlusion.rotate_180.t1.combined.png": "embedded\u002Fc7a92a0d51a565c1ae0bd1b8bee8f52b78c3be1c6a734a97bcfe52a0d2e41491.png",
          "occlusion.rotate_180.t2.combined.png": "embedded\u002Fe05b66299df27d6502853f0eb0180d93f10d29243bfd86be90712b4e8878586d.png",
          "recolor.color_inversion.t1.combined.png": "embedded\u002Fb86752ef36db9079ff07504d0314b980f9c8f3efb78b3b3430afa3420703112e.png",
          "recolor.color_inversion.t2.combined.png": "embedded\u002Fbfb11f28bd23ffbead33e2fb9d4964861e0a1217bbce2e36607ffaa411202eb0.png",
          "recolor.shape_color_mapping.t1.combined.png": "embedded\u002Fbb78d65d83dde425f84a6b38c05f5ce244e3c2d0ec3f3ddd5d459be05ba71da4.png",
          "recolor.shape_color_mapping.t2.combined.png": "embedded\u002Fe3ed462048beb7a6cc27fa02d106ea5caa1ca614cd19d8969d348fc04cb7720d.png",
          "recolor.touching_edges_recolor.t1.combined.png": "embedded\u002F585c28daad25a99d32e11dcbf606d95fcc0deb7bea8191310fb4bcd0ce5853a5.png",
          "recolor.touching_edges_recolor.t2.combined.png": "embedded\u002Fca59e29ea92e55c5a73f4a197a2944ce097ef79b452034f7343772031768a9a1.png"
        },
        "responses": {
          "": ""
        },
        "parameters": {},
        "messageHandlers": {},
        "title": "4. Rule Description - Form"
      }
    },
    {
      "type": "lab.html.Form",
      "content": "\u003Csection class=\"survey-section\" style=\"text-align: center; padding-top: 60px;\"\u003E\n\n  \u003Ch1\u003EThank you!\u003C\u002Fh1\u003E\n\n  \u003Cp style=\"font-size: 1.2rem; margin-top: 30px;\"\u003E\n    You have completed the questionnaire.\n  \u003C\u002Fp\u003E\n\n\u003C\u002Fsection\u003E",
      "scrollTop": true,
      "files": {},
      "responses": {
        "": ""
      },
      "parameters": {},
      "messageHandlers": {
        "run": function anonymous(
) {
const ds = this.options.datastore

const participantId = ds.get('participant_id') || 'unknown'
const date = new Date().toISOString().slice(0, 10)

const filename = `ARC_questionnaire_${participantId}_${date}.csv`

// Emergency backups
console.log('=== LABJS CSV BACKUP ===')
console.log(ds.exportCsv())

console.log('=== LABJS JSON BACKUP ===')
console.log(ds.exportJson())

// Normal save
ds.download('csv', filename)
}
      },
      "title": "5. Thank you"
    }
  ]
})

// Let's go!
study.run()