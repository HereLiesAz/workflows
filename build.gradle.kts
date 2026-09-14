// Top-level build file where you can add configuration options common to all sub-projects/modules.
buildscript {
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://jitpack.io") } // Corrected jitpack reference
    }
    dependencies {
        classpath("com.android.tools.build:gradle:8.13.0") // Corrected classpath syntax
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:2.2.20") // Corrected classpath syntax

        // NOTE: Do not place your application dependencies here; they belong
        // in the individual module build.gradle files
    }
}

tasks.register<Delete>("clean") { // Updated task registration
    delete(rootProject.buildDir)
}
