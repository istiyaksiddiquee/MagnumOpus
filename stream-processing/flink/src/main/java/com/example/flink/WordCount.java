package com.example.flink;

import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.api.java.functions.KeySelector;
import org.apache.flink.api.java.tuple.Tuple2;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.configuration.RestOptions;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.util.Collector;

/**
 * Simple Word Count Flink Application
 * Generates sample text and counts word occurrences
 */
public class WordCount {

    public static void main(String[] args) throws Exception {
        // Use "local" argument to test locally, otherwise connects to remote cluster
        boolean runLocally = args.length > 0 && args[0].equals("local");

        StreamExecutionEnvironment env;

        if (runLocally) {
            // Create local execution environment for testing
            env = StreamExecutionEnvironment.getExecutionEnvironment();
            System.out.println("Running in LOCAL mode");
        } else {
            // Create configuration for remote Flink cluster
            Configuration config = new Configuration();
            config.setString("jobmanager.rpc.address", "192.168.178.50");
            config.setInteger("jobmanager.rpc.port", 6123);
            config.setString(RestOptions.ADDRESS, "192.168.178.50");
            config.setInteger(RestOptions.PORT, 8081);

            // Get the JAR file path
            String jarPath = WordCount.class.getProtectionDomain()
                    .getCodeSource()
                    .getLocation()
                    .toURI()
                    .getPath();

            // Create execution environment connected to remote cluster with JAR
            env = StreamExecutionEnvironment.createRemoteEnvironment(
                    "192.168.178.50",
                    8081,
                    config,
                    jarPath  // Pass the JAR file so remote cluster has access to classes
            );
            System.out.println("Running on REMOTE cluster at 192.168.178.50");
            System.out.println("Using JAR: " + jarPath);
        }

        // Set parallelism
        env.setParallelism(1);

        // Generate sample text stream
        DataStream<String> text = env.fromElements(
                "Apache Flink is a framework and distributed processing engine",
                "Flink provides data distribution, communication, and fault tolerance",
                "Apache Flink is designed for stateful computations over data streams",
                "Flink supports batch and stream processing",
                "The Flink architecture is powerful and flexible"
        );

        // Process: split into words, count occurrences
        DataStream<Tuple2<String, Integer>> wordCounts = text
                .flatMap(new Tokenizer())
                .keyBy(new WordKeySelector())
                .sum(1);

        // Print results
        wordCounts.print();

        // Execute the Flink job
        env.execute("Simple Word Count Example");
    }

    /**
     * Tokenizer that splits sentences into words
     */
    public static final class Tokenizer implements FlatMapFunction<String, Tuple2<String, Integer>> {
        @Override
        public void flatMap(String value, Collector<Tuple2<String, Integer>> out) {
            // Split the line into words
            String[] words = value.toLowerCase().split("\\W+");

            // Emit each word with count 1
            for (String word : words) {
                if (word.length() > 0) {
                    out.collect(new Tuple2<>(word, 1));
                }
            }
        }
    }

    /**
     * KeySelector to extract the word (first field) from the tuple
     */
    public static final class WordKeySelector implements KeySelector<Tuple2<String, Integer>, String> {
        @Override
        public String getKey(Tuple2<String, Integer> value) {
            return value.f0;
        }
    }
}