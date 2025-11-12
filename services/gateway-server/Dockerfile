FROM eclipse-temurin:17-jdk-alpine as build
WORKDIR /app
COPY pom.xml mvnw ./
COPY .mvn .mvn
RUN ./mvnw dependency:resolve

COPY src src
RUN ./mvnw package -DskipTests

FROM eclipse-temurin:17-jre-alpine AS jre
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
ENTRYPOINT ["java","-jar","app.jar"]