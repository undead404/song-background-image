module.exports = {
  env: {
    commonjs: true,
    node: true,
  },
  extends: [
    'airbnb-base',
    'plugin:promise/recommended',
    'plugin:unicorn/recommended',
    'plugin:array-func/all',
    'plugin:lodash/recommended',
    'plugin:node/recommended',
    'plugin:eslint-comments/recommended',
    'plugin:jest/all',
    'prettier',
  ],
  overrides: [
    {
      files: ['scripts/*'],
      rules: {
        'import/no-extraneous-dependencies': [
          'error',
          {
            devDependencies: true,
          },
        ],
        'node/no-unpublished-import': 'off',
      },
    },
    {
      env: {
        'jest/globals': true,
      },
      files: ['**/*.test.js'],
    },
  ],
  parser: 'babel-eslint',
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
  },
  plugins: [
    'prettier',
    'promise',
    'unicorn',
    'array-func',
    'lodash',
    'node',
    'eslint-comments',
    'jest',
  ],
  rules: {
    'no-console': 0,
    'no-param-reassign': ['error', { props: false }],
    'prefer-destructuring': 0,
    'consistent-return': 'off',
    'arrow-body-style': 0,
    'comma-dangle': 0,
    'node/no-unsupported-features/es-syntax': 'off',
    'import/prefer-await-to-then': 'off',
    'no-underscore-dangle': 'off',
    'lodash/prefer-lodash-method': [
      'error',
      {
        ignoreMethods: ['find'],
      },
    ],
    'import/no-unresolved': ['error', { ignore: ['@env'] }],
    'node/no-missing-import': 'off',
    'node/no-unpublished-import': 'off',
  },
};
