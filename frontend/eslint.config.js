// eslint.config.js  (ESLint v9 flat config)
import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      // app.js uses require/module.exports (CommonJS) even though
      // package.json has "type":"module" — ESLint needs to know this
      sourceType: "commonjs",
      globals: {
        require:    "readonly",
        module:     "readonly",
        exports:    "readonly",
        __dirname:  "readonly",
        __filename: "readonly",
        process:    "readonly",
        console:    "readonly",
        setTimeout: "readonly",
        // Browser globals used in views/index.html inline scripts
        window:     "readonly",
        document:   "readonly",
        fetch:      "readonly",
      },
    },
    rules: {
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "no-console":     "off",
      "eqeqeq":         "error",
      "no-var":         "error",
      "prefer-const":   "error",
    },
  },
];