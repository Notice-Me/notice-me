plugins { id("com.android.application") }

android {
    namespace = "ai.noticeme.vehicle"
    compileSdk = 37
    defaultConfig {
        applicationId = "ai.noticeme.vehicle"
        minSdk = 28
        targetSdk = 34
        versionCode = 13
        versionName = "0.3.7"
    }
    flavorDimensions += "speech"
    productFlavors {
        create("pleos") { dimension = "speech" }
        create("standard") {
            dimension = "speech"
            applicationIdSuffix = ".standard"
        }
    }
    buildFeatures { buildConfig = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    testOptions { unitTests.isReturnDefaultValues = true }
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.google.code.gson:gson:2.10.1")
    "pleosImplementation"("ai.pleos.playground:TextToSpeech:3.3.1")
    "pleosImplementation"("ai.pleos.playground:NaviHelper:3.0.5")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
    testImplementation("com.squareup.okhttp3:mockwebserver:4.12.0")
}
