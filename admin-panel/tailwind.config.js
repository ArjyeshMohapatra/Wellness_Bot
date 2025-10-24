/** @type {import('tailwindcss').Config} */ //gives editor inteliSense and type checking ability to suggest classes
export default { // helps in auto completion in editors
  content: [ // scans for all the files in which tailwind is to be implemented
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {}, // tells not to override tailwinds default values
  },
  plugins: [], // register 1st or 3rd party tailwind plugins for additional utilities or components
}